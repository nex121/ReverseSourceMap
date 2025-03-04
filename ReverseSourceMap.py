import json
import os
import sys
import base64
import urllib.request
from urllib.parse import urljoin
import re


class ReverseSourceMap:
    def __init__(self, output_dir="./output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def extract_sourcemap_url(self, js_content):
        """从JS文件内容中提取sourcemap URL"""
        lines = js_content.splitlines()
        for line in lines:
            if "//# sourceMappingURL=" in line:
                return line.split("//# sourceMappingURL=")[1].strip()
        return None

    def fetch_file(self, url):
        """从URL获取文件内容"""
        try:
            response = urllib.request.urlopen(url)
            return response.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def sanitize_path(self, path):
        """清理文件路径，移除不合法字符和协议前缀"""
        # 移除 webpack:// 和 file:// 等协议前缀
        path = re.sub(r'^(webpack|file|https?):/{1,2}', '', path)

        # 移除 node_modules, ~, @ 等常见前缀
        path = re.sub(r'^(~|node_modules/|@)', '', path)

        # 替换不合法字符
        path = re.sub(r'[<>:"|?*]', '_', path)

        # 移除前导斜杠，避免绝对路径
        path = path.lstrip('/')

        # 确保路径不为空且不超出当前目录
        if not path or path.startswith('..'):
            path = 'unknown_source.js'

        return path

    def process_sourcemap(self, sourcemap_content, base_url):
        """处理sourcemap内容并还原源文件"""
        try:
            sourcemap = json.loads(sourcemap_content)

            # 创建源文件目录
            sanitized_sources = []
            for source in sourcemap.get('sources', []):
                # 清理和处理路径
                sanitized_source = self.sanitize_path(source)
                sanitized_sources.append(sanitized_source)

                source_dir = os.path.dirname(sanitized_source)
                output_dir = os.path.join(self.output_dir, source_dir)

                if source_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)

            # 提取源代码
            if 'sourcesContent' in sourcemap and sourcemap['sourcesContent']:
                for i, source in enumerate(sourcemap.get('sources', [])):
                    if i < len(sourcemap['sourcesContent']):
                        source_content = sourcemap['sourcesContent'][i]
                        if source_content:
                            sanitized_source = sanitized_sources[i]
                            output_path = os.path.join(self.output_dir, sanitized_source)

                            # 确保目录存在
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)

                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(source_content)
                            print(f"Extracted: {sanitized_source} (from {source})")

            # 如果没有sourcesContent，尝试从sourceRoot和sources组合的URL获取
            elif 'sourceRoot' in sourcemap:
                source_root = sourcemap['sourceRoot']
                for i, source in enumerate(sourcemap.get('sources', [])):
                    try:
                        source_url = urljoin(urljoin(base_url, source_root), source)
                        source_content = self.fetch_file(source_url)

                        if source_content:
                            sanitized_source = sanitized_sources[i]
                            output_path = os.path.join(self.output_dir, sanitized_source)

                            # 确保目录存在
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)

                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(source_content)
                            print(f"Fetched and extracted: {sanitized_source} (from {source})")
                    except Exception as e:
                        print(f"Error fetching source {source}: {e}")

            return True
        except Exception as e:
            print(f"Error processing sourcemap: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_inline_sourcemap(self, sourcemap_url):
        """处理内联的sourcemap"""
        # 处理base64编码的内联sourcemap
        if sourcemap_url.startswith("data:application/json;base64,"):
            base64_data = sourcemap_url.replace("data:application/json;base64,", "")
            try:
                sourcemap_content = base64.b64decode(base64_data).decode('utf-8')
                return self.process_sourcemap(sourcemap_content, "")
            except Exception as e:
                print(f"Error decoding inline sourcemap: {e}")
                return False
        return False

    def extract_from_js_url(self, js_url):
        """从JS URL中提取源码"""
        js_content = self.fetch_file(js_url)
        if not js_content:
            return False

        sourcemap_url = self.extract_sourcemap_url(js_content)
        if not sourcemap_url:
            print(f"No sourcemap URL found in {js_url}")
            return False

        # 处理内联sourcemap
        if sourcemap_url.startswith("data:"):
            return self.process_inline_sourcemap(sourcemap_url)

        # 处理相对URL
        if not sourcemap_url.startswith(("http://", "https://")):
            sourcemap_url = urljoin(js_url, sourcemap_url)

        sourcemap_content = self.fetch_file(sourcemap_url)
        if not sourcemap_content:
            return False

        base_url = os.path.dirname(sourcemap_url) + "/"
        return self.process_sourcemap(sourcemap_content, base_url)

    def extract_from_sourcemap_url(self, sourcemap_url):
        """直接从sourcemap URL中提取源码"""
        sourcemap_content = self.fetch_file(sourcemap_url)
        if not sourcemap_content:
            return False

        base_url = os.path.dirname(sourcemap_url) + "/"
        return self.process_sourcemap(sourcemap_content, base_url)

    def extract_from_local_js(self, js_path):
        """从本地JS文件中提取源码"""
        try:
            with open(js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()

            sourcemap_url = self.extract_sourcemap_url(js_content)
            if not sourcemap_url:
                print(f"No sourcemap URL found in {js_path}")
                return False

            # 处理内联sourcemap
            if sourcemap_url.startswith("data:"):
                return self.process_inline_sourcemap(sourcemap_url)

            # 处理本地文件或URL
            if sourcemap_url.startswith(("http://", "https://")):
                sourcemap_content = self.fetch_file(sourcemap_url)
                base_url = os.path.dirname(sourcemap_url) + "/"
            else:
                # 假设sourcemap相对于JS文件路径
                sourcemap_path = os.path.join(os.path.dirname(js_path), sourcemap_url)
                try:
                    with open(sourcemap_path, 'r', encoding='utf-8') as f:
                        sourcemap_content = f.read()
                    base_url = os.path.dirname(os.path.abspath(sourcemap_path)) + "/"
                except:
                    print(f"Cannot read sourcemap file: {sourcemap_path}")
                    return False

            return self.process_sourcemap(sourcemap_content, base_url)

        except Exception as e:
            print(f"Error processing local JS file: {e}")
            return False

    def extract_from_local_sourcemap(self, sourcemap_path):
        """从本地sourcemap文件中提取源码"""
        try:
            with open(sourcemap_path, 'r', encoding='utf-8') as f:
                sourcemap_content = f.read()

            base_url = os.path.dirname(os.path.abspath(sourcemap_path)) + "/"
            return self.process_sourcemap(sourcemap_content, base_url)

        except Exception as e:
            print(f"Error processing local sourcemap file: {e}")
            return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python reverse_sourcemap.py [js|sourcemap] [url|file_path] [output_dir]")
        return

    file_type = sys.argv[1]
    path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "./output"

    extractor = ReverseSourceMap(output_dir)

    if file_type == "js":
        if path.startswith(("http://", "https://")):
            extractor.extract_from_js_url(path)
        else:
            extractor.extract_from_local_js(path)
    elif file_type == "sourcemap":
        if path.startswith(("http://", "https://")):
            extractor.extract_from_sourcemap_url(path)
        else:
            extractor.extract_from_local_sourcemap(path)
    else:
        print("Invalid file type. Use 'js' or 'sourcemap'.")


if __name__ == "__main__":
    main()
