import React from 'react';

/**
 * A robust, zero-dependency Markdown parser that converts Markdown string
 * into structured JSX elements to render in React.
 */
export default function MarkdownRenderer({ content }) {
  if (!content) return null;

  const parseInline = (text) => {
    if (!text) return "";
    
    // Escape HTML tags to prevent XSS, but allow custom tags we introduce
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Bold formatting: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Italic formatting: *text*
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    
    // Inline code: `code`
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");

    return <span dangerouslySetInnerHTML={{ __html: html }} />;
  };

  const lines = content.split('\n');
  const elements = [];
  let inList = false;
  let listItems = [];
  let listType = 'ul'; // 'ul' or 'ol'
  let inCodeBlock = false;
  let codeBlockContent = [];
  let codeLang = '';
  let inTable = false;
  let tableRows = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code blocks
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${i}`} className="markdown-pre">
            {codeLang && <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 8, fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase' }}>{codeLang}</div>}
            <code>{codeBlockContent.join('\n')}</code>
          </pre>
        );
        inCodeBlock = false;
        codeBlockContent = [];
      } else {
        inCodeBlock = true;
        codeLang = line.replace('```', '').trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Tables
    if (line.trim().startsWith('|')) {
      if (!inTable) {
        if (inList) {
          elements.push(renderList(listItems, listType, i));
          inList = false;
          listItems = [];
        }
        inTable = true;
        tableRows = [];
      }
      
      // Skip separator rows like |---|---|
      if (line.includes('-') && !line.match(/[a-zA-Z0-9]/)) {
        continue;
      }
      
      const cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      elements.push(renderTable(tableRows, i));
      inTable = false;
      tableRows = [];
    }

    // Lists (unordered)
    const isUnordered = line.trim().startsWith('* ') || line.trim().startsWith('- ');
    const isOrdered = /^\d+\.\s/.test(line.trim());

    if (isUnordered || isOrdered) {
      const currentType = isUnordered ? 'ul' : 'ol';
      const cleanText = isUnordered 
        ? line.trim().substring(2) 
        : line.trim().replace(/^\d+\.\s/, '');

      if (!inList) {
        inList = true;
        listType = currentType;
        listItems = [];
      } else if (listType !== currentType) {
        elements.push(renderList(listItems, listType, i));
        listType = currentType;
        listItems = [];
      }
      listItems.push(cleanText);
      continue;
    } else if (inList) {
      elements.push(renderList(listItems, listType, i));
      inList = false;
      listItems = [];
    }

    // Headings (#### → h4, ### → h3, ## → h2, # → h1)
    if (line.trim().startsWith('#### ')) {
      elements.push(<h4 key={i} className="markdown-h4">{parseInline(line.trim().substring(5))}</h4>);
      continue;
    } else if (line.trim().startsWith('### ')) {
      elements.push(<h3 key={i} className="markdown-h3">{parseInline(line.trim().substring(4))}</h3>);
      continue;
    } else if (line.trim().startsWith('## ')) {
      elements.push(<h2 key={i} className="markdown-h2">{parseInline(line.trim().substring(3))}</h2>);
      continue;
    } else if (line.trim().startsWith('# ')) {
      elements.push(<h1 key={i} className="markdown-h1">{parseInline(line.trim().substring(2))}</h1>);
      continue;
    }

    // Blockquotes
    if (line.trim().startsWith('> ')) {
      elements.push(
        <blockquote key={i} className="markdown-blockquote">
          {parseInline(line.trim().substring(2))}
        </blockquote>
      );
      continue;
    }

    // Horizontal Rule
    if (line.trim() === '---' || line.trim() === '***') {
      elements.push(<hr key={i} className="markdown-hr" />);
      continue;
    }

    // Empty lines
    if (line.trim() === '') {
      continue;
    }

    // Regular paragraphs
    elements.push(<p key={i} className="markdown-p">{parseInline(line)}</p>);
  }

  // Handle trailing states
  if (inTable && tableRows.length > 0) {
    elements.push(renderTable(tableRows, lines.length));
  }
  if (inList && listItems.length > 0) {
    elements.push(renderList(listItems, listType, lines.length));
  }
  if (inCodeBlock && codeBlockContent.length > 0) {
    elements.push(
      <pre key={`code-end`} className="markdown-pre">
        <code>{codeBlockContent.join('\n')}</code>
      </pre>
    );
  }

  function renderList(items, type, keyIdx) {
    const Tag = type;
    return (
      <Tag key={`list-${keyIdx}`} className={`markdown-${type}`}>
        {items.map((item, idx) => (
          <li key={idx} className="markdown-li">{parseInline(item)}</li>
        ))}
      </Tag>
    );
  }

  function renderTable(rows, keyIdx) {
    if (rows.length === 0) return null;
    const headerRow = rows[0];
    const bodyRows = rows.slice(1);
    return (
      <div key={`table-wrapper-${keyIdx}`} className="table-container">
        <table className="markdown-table">
          <thead>
            <tr>
              {headerRow.map((cell, idx) => <th key={idx} className="markdown-th">{parseInline(cell)}</th>)}
            </tr>
          </thead>
          <tbody>
            {bodyRows.map((row, rIdx) => (
              <tr key={rIdx} className="markdown-tr">
                {row.map((cell, cIdx) => <td key={cIdx} className="markdown-td">{parseInline(cell)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return <div className="markdown-renderer-body">{elements}</div>;
}
