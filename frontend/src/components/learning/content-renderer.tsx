import React, { useEffect } from 'react'

interface ContentRendererProps {
  content: string
  onHeadingsFound?: (headings: { id: string; text: string; level: number }[]) => void
}

export function ContentRenderer({ content, onHeadingsFound }: ContentRendererProps) {
  const processedContent = React.useMemo(() => {
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = content

    function findTextNodes(element: Element | Document): Text[] {
      const textNodes: Text[] = [];
      const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null
      );
      
      let node;
      while (node = walker.nextNode()) {
        if (node.textContent && node.textContent.trim() !== '') {
          let parent = node.parentElement;
          let skipProcessing = false;
          
          while (parent) {
            if (['PRE', 'CODE'].includes(parent.tagName)) {
              skipProcessing = true;
              break;
            }
            parent = parent.parentElement;
          }
          
          if (!skipProcessing) {
            textNodes.push(node as Text);
          }
        }
      }
      
      return textNodes;
    }
    
    const textNodes = findTextNodes(tempDiv);
    textNodes.forEach(textNode => {
      const text = textNode.textContent || '';
      
      const hasLongWord = text.split(/\s+/).some(word => word.length > 20);
      
      if (hasLongWord) {
        const container = document.createElement('span');
        container.style.wordBreak = 'break-all';
        container.style.overflowWrap = 'break-word';
        container.style.maxWidth = '100%';
        container.style.display = 'inline-block';
        container.classList.add('break-long-words');
        
        const fragment = document.createDocumentFragment();
        const words = text.split(/\s+/);
        
        for (let i = 0; i < words.length; i++) {
          const word = words[i];
          
          if (word.length > 20) {
            for (let j = 0; j < word.length; j++) {
              fragment.appendChild(document.createTextNode(word[j]));
              
              if (j < word.length - 1 && (j + 1) % 10 === 0) {
                fragment.appendChild(document.createTextNode('\u200B'));
              }
            }
          } else {
            fragment.appendChild(document.createTextNode(word));
          }
          
          if (i < words.length - 1) {
            fragment.appendChild(document.createTextNode(' '));
          }
        }
        
        container.appendChild(fragment);
        
        if (textNode.parentNode) {
          textNode.parentNode.replaceChild(container, textNode);
        }
      }
    });
    
    const headings = Array.from(tempDiv.querySelectorAll('h1, h2, h3')).map(heading => {
      const id = heading.textContent?.toLowerCase().replace(/\s+/g, '-') ?? ''
      heading.id = id
      return {
        id,
        text: heading.textContent ?? '',
        level: parseInt(heading.tagName[1])
      }
    })
    
    return {
      html: tempDiv.innerHTML,
      headings
    }
  }, [content])

  useEffect(() => {
    if (onHeadingsFound) {
      onHeadingsFound(processedContent.headings)
    }
  }, [processedContent.headings, onHeadingsFound])

  useEffect(() => {
    let styleEl = document.getElementById('word-break-styles');
    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = 'word-break-styles';
      document.head.appendChild(styleEl);
    }
    
    styleEl.textContent = `
      .break-long-words {
        word-break: break-all !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        -ms-word-break: break-all !important;
        max-width: 100%;
      }
    `;
    
    return () => {
      if (styleEl && document.head.contains(styleEl)) {
        document.head.removeChild(styleEl);
      }
    };
  }, []);

  return (
    <article 
      className="prose prose-gray max-w-none
        prose-headings:scroll-mt-16
        prose-h1:font-extrabold prose-h1:text-3xl prose-h1:mt-8 prose-h1:mb-4
        prose-h2:font-bold prose-h2:text-2xl prose-h2:mt-6 prose-h2:mb-3
        prose-h3:font-semibold prose-h3:text-xl prose-h3:mt-4 prose-h3:mb-2
        prose-p:text-gray-600 prose-p:leading-relaxed prose-p:mb-4
        prose-strong:text-gray-900 prose-strong:font-semibold
        prose-ul:list-disc prose-ul:list-outside prose-ul:ml-4 prose-ul:my-4 prose-ul:space-y-2
        prose-ol:list-decimal prose-ol:list-outside prose-ol:ml-4 prose-ol:my-4 prose-ol:space-y-2
        prose-li:text-gray-600 prose-li:pl-2
        break-words"
      style={{ 
        maxWidth: '100%'
      }}
      dangerouslySetInnerHTML={{ __html: processedContent.html }}
    />
  )
}