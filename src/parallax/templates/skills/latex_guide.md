---
name: latex-guide
description: LaTeX and BibTeX troubleshooting guide. Error patterns, fixes, best practices.
---

# /latex-guide -- LaTeX/BibTeX Troubleshooting

> Practical reference for common LaTeX errors, BibTeX workflow, and Beamer specifics.

## When to Use

Consult when encountering LaTeX compilation errors, bibliography issues, or package conflicts. Auto-invocable by writing agents when LaTeX errors arise.

## Common Error Patterns

### Compilation Errors

| Error | Cause | Fix |
|---|---|---|
| `Undefined control sequence` | Unknown command or missing package | Add `\usepackage{package}` or fix typo |
| `Missing $ inserted` | Math symbol outside math mode | Wrap in `$...$` or `\(...\)` |
| `File not found` | Wrong path or missing file | Check `\includegraphics` / `\input` paths |
| `Too many }'s` | Brace mismatch | Count braces; use editor matching |
| `Overfull \hbox` | Content exceeds margins | Rephrase, resize figure, or use `\adjustbox` |
| `Missing \begin{document}` | Preamble error before `\begin{document}` | Check for syntax errors in preamble |
| `Float(s) lost` | Float in restricted context | Move float to top level or use `[H]` placement |

### BibTeX Errors

| Error | Cause | Fix |
|---|---|---|
| `Citation undefined` | Missing bib entry or wrong key | Verify key exists in `.bib` file |
| `Empty bibliography` | Wrong `.bib` path or no `\cite{}` | Check `\bibliography{file}` path |
| `I found no \citation commands` | `\cite{}` not in document | Ensure citations exist before `\bibliography` |

### Compilation Workflow

```bash
# Standard workflow (handles cross-references)
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

# Or use latexmk (automates the cycle)
latexmk -pdf main.tex
```

Always compile at least twice after adding citations or cross-references.

## Package Conflict Resolution

Common conflicts and fixes:
- `hyperref` should be loaded **last** (with few exceptions like `cleveref`)
- `cleveref` must load **after** `hyperref`
- `biblatex` and `natbib` are mutually exclusive -- choose one
- `inputenc` with `utf8` is default in modern LaTeX; remove if using LuaLaTeX/XeLaTeX
- `geometry` and `fullpage` conflict -- use only `geometry`

## Figure Best Practices

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\columnwidth]{figures/result.pdf}
  \caption{Description of what the figure shows.}
  \label{fig:result}
\end{figure}
```

- Use PDF/EPS for vector graphics, PNG for rasters
- Use relative paths from project root
- Always include `\label` after `\caption`
- Reference with `\ref{fig:result}` or `\autoref{fig:result}`

## Cross-Referencing

- `\label{}` must come **after** `\caption{}` in floats
- Use `\ref{}`, `\eqref{}`, `\autoref{}`, or `\cref{}` (cleveref)
- Run twice to resolve forward references
- Check log for `LaTeX Warning: Reference ... undefined`

## Beamer Specifics

### Frame Structure
```latex
\begin{frame}{Frame Title}
  Content here. Keep it minimal.
\end{frame}
```

### Common Beamer Issues
- `Overfull` in frames: use `\begin{frame}[shrink]` or reduce content
- Fragile content (verbatim, listings): use `\begin{frame}[fragile]`
- Animation: `\pause`, `\only<N>{...}`, `\onslide<N>{...}`
- Theme: set once in preamble (`\usetheme{Madrid}`, `\usecolortheme{default}`)

### Beamer + BibTeX
```latex
% In preamble
\usepackage[style=authoryear]{biblatex}
\addbibresource{refs.bib}

% At end, before \end{document}
\begin{frame}[allowframebreaks]{References}
  \printbibliography
\end{frame}
```

## Protocol

- When a LaTeX error occurs, check this guide first before searching externally.
- Fix errors immediately after compilation -- don't accumulate.
- Compile frequently: after each section, not just at the end.
- Check the `.log` file for warnings, not just errors.
