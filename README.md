# ReverseSourceMap

ReverseSourceMap 是一个用于从 JavaScript sourcemap 中还原原始源码的 Python 脚本。该工具支持从内联或外部 sourcemap 中提取源码，并自动将源码保存到指定的输出目录中，便于调试和代码分析。

---

## 功能

- **自动提取 sourcemap URL：** 从 JS 文件中识别 `//# sourceMappingURL=` 注释，提取 sourcemap 的位置。
- **内联 sourcemap 解析：** 支持处理内联（Base64 编码）的 sourcemap，自动解码并解析 JSON 数据。
- **远程与本地支持：** 可直接处理 URL 或本地文件，无论是 JS 文件还是 sourcemap 文件。
- **源码还原：**  
  - 当 sourcemap 包含 `sourcesContent` 字段时，直接使用其中嵌入的源码。  
  - 当 sourcemap 不包含 `sourcesContent` 时，通过 `sourceRoot` 与 `sources` 字段构造完整 URL 并获取源码。
- **安全的文件路径处理：** 清理和标准化文件路径，移除非法字符和不安全的前缀（如 `webpack://`、`file://`、`node_modules/` 等）。
- **自动创建目录：** 根据源码文件的目录结构自动在输出目录中创建相应的文件夹，确保源码文件有序保存。

---

## 依赖

- Python 3.x
- 使用了 Python 标准库模块：
  - `json`
  - `os`
  - `sys`
  - `base64`
  - `urllib.request`
  - `re`
  - `urllib.parse`

---

## 使用方法

ReverseSourceMap 脚本通过命令行参数运行，支持两种模式：从 JS 文件提取或直接处理 sourcemap 文件。

### 命令行参数格式

```bash
python reverse_sourcemap.py [js|sourcemap] [url|file_path] [output_dir]
```
- [js|sourcemap]

  - js：表示输入为 JavaScript 文件，脚本将从中提取 sourcemap URL。
  - sourcemap：表示输入为 sourcemap 文件，直接进行源码提取。
- [url|file_path]

  - 支持 URL（以 http:// 或 https:// 开头）或本地文件路径。
- [output_dir] （可选）

  - 指定输出目录，默认值为 ./output。


### 示例
从远程 JS 文件中提取 sourcemap 并还原源码：

```bash
python reverse_sourcemap.py js https://example.com/static/app.js ./output
```
从本地 JS 文件中提取 sourcemap 并还原源码：
```bash
python reverse_sourcemap.py js ./path/to/app.js ./output
```
直接从远程 sourcemap 文件中还原源码：

```bash
python reverse_sourcemap.py sourcemap https://example.com/static/app.js.map ./output
```
直接从本地 sourcemap 文件中还原源码：

```bash
python reverse_sourcemap.py sourcemap ./path/to/app.js.map ./output
```

![image](https://github.com/user-attachments/assets/3ee0abf0-01d2-4e15-bcd9-fd7bcb23ab9c)

![image](https://github.com/user-attachments/assets/f28c7c98-554d-49b5-9a17-56685c61fecf)

