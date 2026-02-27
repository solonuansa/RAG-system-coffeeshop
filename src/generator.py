import time
import logging
from groq import Groq
from groq import APIError, RateLimitError
from typing import Optional
from config.settings import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT, API_TIMEOUT, MAX_RETRIES, RETRY_DELAY, CONTEXT_PROMPT_TEMPLATE

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Generator:
    """Menangani generate teks menggunakan Groq API"""
    
    def __init__(self, api_key: str = None, model: str = GROQ_MODEL):
        """
        Inisialisasi generator dengan Groq
        
        Args:
            api_key: API key Groq
            model: Nama model yang digunakan
        """
        self.api_key = api_key or GROQ_API_KEY
        self.model = model
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY tidak ditemukan. Silakan set di environment variables.")
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
    
    def generate(
        self, 
        query: str, 
        context: str,
        system_prompt: str = SYSTEM_PROMPT,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE
    ) -> str:
        """
        Generate response menggunakan Groq dengan retry logic
        
        Args:
            query: Query dari user
            context: Konteks yang diambil dari vector store
            system_prompt: System prompt untuk model
            max_tokens: Maksimal token yang di-generate
            temperature: Temperature sampling
            
        Returns:
            Teks response yang di-generate
        """
        user_message = CONTEXT_PROMPT_TEMPLATE.format(context=context, query=query)
        
        for attempt in range(MAX_RETRIES):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=API_TIMEOUT
                )
                
                response = chat_completion.choices[0].message.content
                return response
                
            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return "Maaf, terlalu banyak permintaan. Silakan coba lagi nanti."
                    
            except APIError as e:
                logger.error(f"Groq API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return "Maaf, terjadi kesalahan pada API. Silakan coba lagi nanti."
                    
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{MAX_RETRIES}): {e}", exc_info=True)
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return f"Error: {str(e)}"
        
        return "Maaf, gagal menghasilkan respons setelah beberapa percobaan."
    
    def generate_simple(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        """
        Generate sederhana tanpa konteks RAG dengan retry logic
        
        Args:
            prompt: Prompt langsung ke model
            max_tokens: Maksimal token yang di-generate
            
        Returns:
            Teks yang di-generate
        """
        for attempt in range(MAX_RETRIES):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    max_tokens=max_tokens,
                    timeout=API_TIMEOUT
                )
                
                return chat_completion.choices[0].message.content
                
            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return "Maaf, terlalu banyak permintaan. Silakan coba lagi nanti."
                    
            except APIError as e:
                logger.error(f"Groq API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return "Maaf, terjadi kesalahan pada API. Silakan coba lagi nanti."
                    
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}/{MAX_RETRIES}): {e}", exc_info=True)
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    logger.info(f"Menunggu {wait_time} detik sebelum mencoba lagi...")
                    time.sleep(wait_time)
                else:
                    return f"Error: {str(e)}"
        
        return "Maaf, gagal menghasilkan respons setelah beberapa percobaan."
