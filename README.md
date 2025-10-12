# CropCare-
CropCare is an AI-powered web application designed to assist with agricultural analysis. It allows users to upload documents and images related to farming and receive instant insights, summaries, and answers to their questions in multiple language.

Core Features
Multilingual Support: The application operates in four languages: English, Hindi, Telugu, and Malayalam, making it accessible to a diverse user base.

Image Analysis: Users can upload images of crops to identify potential diseases or pests. The AI provides an analysis and suggests solutions. 📸

Document Processing: It can extract and understand text from various document formats, including PDFs (even scanned ones), DOCX, and TXT files. This is useful for summarizing soil reports, farming guides, or other agricultural documents.

Interactive Chat: After an analysis is generated, users can ask follow-up questions about the document or image in a conversational chat interface.

General Q&A: A separate tab allows users to ask any general agricultural questions, functioning as an AI expert for farming topics.

Technology
CropCare is built using Python and Streamlit. It operates as a service using a single, secure OpenRouter API key configured on the backend.

Text Analysis: Powered by meta-llama/llama-3-8b-instruct:free, a fast and efficient model for summarizing documents and handling chat conversations.

Vision and OCR: Uses qwen/qwen2.5-vl-32b-instruct:free for all image-related tasks, including analyzing crop photos and performing Optical Character Recognition (OCR) on scanned documents.
