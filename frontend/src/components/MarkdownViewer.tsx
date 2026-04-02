import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
interface MarkdownViewerProps {
  content: string;
}
const MarkdownViewer = ({ content }: MarkdownViewerProps) => (
  <ReactMarkdown
    rehypePlugins={[rehypeHighlight]}
    components={{
      code({ node, className, children, ...props }) {
        return <code className={className} {...props}>{children}</code>;
      }
    }}
  >
    {content}
  </ReactMarkdown>
);

export default MarkdownViewer;