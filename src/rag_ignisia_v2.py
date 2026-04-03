# !pip install unstructured openpyxl
# !pip install msoffcrypto
# !pip install langchain-community
# !pip install docx2txt
# !pip install langchain-text-splitters
# !pip install langchain-core
# !pip install langchain-openai
# !pip install faiss-cpu
# !pip install transformers accelerate
# !pip install -U transformers
# !pip install langchain-huggingface
# !pip install --upgrade transformers huggingface_hub
# !pip install langchain-google-genai

import pandas as pd
from transformers import pipeline

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain_huggingface import HuggingFacePipeline


import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

pdf_loader = PyPDFLoader("dataset\Meridian_CompanyPolicyManual_v4.2_20250301.pdf")
pdf_docs = pdf_loader.load()

for doc in pdf_docs:
    doc.metadata["source"] = "pdf"


docx_loader = Docx2txtLoader("dataset\Meridian_Email_Simulation.docx")
docx_docs = docx_loader.load()

for doc in docx_docs:
    doc.metadata["source"] = "docx"

xls = pd.ExcelFile("dataset\Meridian_SCM_Dataset (1).xlsx")
excel_docs = []

def clean_row(row):
    return " | ".join([
        f"{col}: {row[col]}"
        for col in row.index
        if "Unnamed" not in col and pd.notna(row[col])
    ])

for sheet in xls.sheet_names:
    df = xls.parse(sheet)
    for i, row in df.iterrows():
        excel_docs.append(
            Document(
                page_content=clean_row(row),
                metadata={
                    "source": "excel",
                    "sheet": sheet,
                    "row": i
                }
            )
        )

# Combining all documents into one
all_docs = excel_docs + pdf_docs + docx_docs

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

final_chunks = []

for doc in all_docs:
    if doc.metadata.get("source") == "excel":
        final_chunks.append(doc)
    else:
        final_chunks.extend(splitter.split_documents([doc]))

print("Total chunks:", len(final_chunks))

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


vectorstore = FAISS.from_documents(final_chunks, embeddings)
vectorstore.save_local("faiss_index")

retriever = vectorstore.as_retriever(search_kwargs={"k": 7})
API_KEY = "YOUR_API_KEY"
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=API_KEY,
    temperature=0.45
)

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an expert business analyst assistant specializing in supply chain, operations, and enterprise data interpretation.

Your task is to answer the user’s question STRICTLY using the provided context.

---------------------
INSTRUCTIONS:
---------------------

1. SOURCE OF TRUTH
- Use ONLY the given context.
- Do NOT use prior knowledge or assumptions.
- If the answer is not explicitly present, respond:
  "I don't know based on the provided data."

2. DATA INTERPRETATION
- The context may contain:
  • Policy documents (textual)
  • Excel-like structured data (rows, fields)
  • Mixed or noisy formatting
- Identify and extract ONLY relevant information.

3. HANDLING STRUCTURED DATA (VERY IMPORTANT)
- Treat each row as a factual record.
- Carefully interpret numerical values (e.g., revenue, quantity, percentages).
- Do NOT approximate or infer missing numbers.

4. IGNORE NOISE
- Ignore irrelevant elements such as:
  • "Unnamed" fields
  • null / nan values
  • formatting artifacts
  • unrelated tables or entries

5. ANSWER FORMAT
- Provide a clear, structured answer using bullet points.
- Keep it concise but complete.
- If applicable, group information logically (e.g., principles, categories, steps).

6. TRACEABILITY (IMPORTANT)
- Base every point directly on the context.
- Do NOT hallucinate or generalize beyond given data.

---------------------
CONTEXT:
{context}
---------------------

QUESTION:
{question}

---------------------
ANSWER:
"""
)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True
)

query = "Explain each operational policies as of 2024"

result = qa.invoke({"query": query})

print("\n===== ANSWER =====")
print(result["result"])

print("\n===== SOURCES =====")
for doc in result["source_documents"]:
    print(doc.metadata)

