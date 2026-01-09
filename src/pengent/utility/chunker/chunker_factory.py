from typing import List, Optional, Union
from ...type.rag import SimpleFAQRagFormat, DocStructuredRagFormat
from .text.text_chunker import TextChunker
from .block.block_chunker import BlockChunker
from .block.markdown_parser import MarkdownBlockParser
from .block.html_parser import HttpBlockParser
from .block.pdf_parser import PdfBlockParser
from .faq.text_faq_parser import TextFAQParser
from .faq.pdf_faq_parser import PdfFAQParser
from .faq.faq_analyzer import FAQAnalyser, FAQAnalysisConfig


def create_format(
    rag_format_type: str,
    file_type: str,
    content,
    parser_config: dict = None,
    source_url: Optional[str] = None,
) -> List[Union[SimpleFAQRagFormat, DocStructuredRagFormat]]:
    # FaqかDocumentのいずれか
    if rag_format_type == "SimpleFAQRagFormat":
        if file_type == "text":
            blocks = TextFAQParser.parse(content)
            analysis_config = FAQAnalysisConfig(**parser_config)
            analyzer = FAQAnalyser(config=analysis_config, source_url=source_url)
            faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks)
            simple_faqs = analyzer.to_simple_faq_format(faq_pairs)
            return simple_faqs
        elif file_type == "markdown":
            blocks = MarkdownBlockParser.parse(content)
            analysis_config = FAQAnalysisConfig(**parser_config)
            analyzer = FAQAnalyser(config=analysis_config, source_url=source_url)
            faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks)
            simple_faqs = analyzer.to_simple_faq_format(faq_pairs)
            return simple_faqs
        elif file_type == "html":
            blocks = HttpBlockParser.parse(content)
            analysis_config = FAQAnalysisConfig(**parser_config)
            analyzer = FAQAnalyser(config=analysis_config, source_url=source_url)
            faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks)
            simple_faqs = analyzer.to_simple_faq_format(faq_pairs)
            return simple_faqs
        elif file_type == "pdf":
            blocks = PdfFAQParser.parse(content)
            analysis_config = FAQAnalysisConfig(**parser_config)
            analyzer = FAQAnalyser(config=analysis_config, source_url=source_url)
            faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks)
            simple_faqs = analyzer.to_simple_faq_format(faq_pairs)
            return simple_faqs
    elif rag_format_type == "DocStructuredRagFormat":
        if file_type == "text":
            chunker = TextChunker(**parser_config)
            chunkers = chunker.split(content)
            docs = chunker.to_doc_structured_format(chunkers)
            return docs
        elif file_type == "markdown":
            blocks = MarkdownBlockParser.parse(content)
            chunker = BlockChunker(**parser_config)
            chunkers = chunker.split(blocks)
            docs = chunker.to_doc_structured_format(chunkers)
            return docs
        elif file_type == "html":
            blocks = HttpBlockParser.parse(content)
            chunker = BlockChunker(**parser_config)
            chunkers = chunker.split(blocks)
            docs = chunker.to_doc_structured_format(chunkers)
            return docs
        elif file_type == "pdf":
            blocks = PdfBlockParser.parse(content)
            chunker = BlockChunker(**parser_config)
            chunkers = chunker.split(blocks)
            docs = chunker.to_doc_structured_format(chunkers)
            return docs
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    else:
        raise ValueError(f"Unsupported rag_format type: {rag_format_type}")
