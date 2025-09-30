// Simple local LLM client
const LLM_CONFIG = {
  baseURL: process.env.LLM_BASE_URL || 'http://localhost:11434/v1',
  apiKey: process.env.LLM_API_KEY || 'dummy-key',
  model: process.env.LLM_MODEL || 'llama2',
  temperature: 0.7,
  maxTokens: 2048,
};

async function callLocalLLM(messages: any[]): Promise<string> {
  try {
    const response = await fetch(`${LLM_CONFIG.baseURL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${LLM_CONFIG.apiKey}`,
      },
      body: JSON.stringify({
        model: LLM_CONFIG.model,
        messages: messages,
        temperature: LLM_CONFIG.temperature,
        max_tokens: LLM_CONFIG.maxTokens,
      }),
    });

    if (!response.ok) {
      throw new Error(`LLM request failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
  } catch (error) {
    console.error('Local LLM error:', error);
    throw new Error('Failed to get response from local LLM');
  }
}

export async function generateResponse(question: string, context: string): Promise<string> {
  try {
    const prompt = `You are a helpful AI assistant that answers questions based on the provided context from PDF documents.

Context:
${context}

Question: ${question}

Please provide a comprehensive answer based on the context. If the context doesn't contain enough information to answer the question, please say so and suggest what additional information might be helpful.

Answer:`;

    const messages = [
      {
        role: 'system',
        content: 'You are a helpful AI assistant that answers questions based on provided context from PDF documents.'
      },
      {
        role: 'user',
        content: prompt
      }
    ];
    
    const response = await callLocalLLM(messages);
    return response;
  } catch (error) {
    console.error('LLM generation error:', error);
    throw new Error('Failed to generate response from LLM');
  }
}

export async function summarizeDocument(text: string): Promise<string> {
  try {
    const prompt = `Please provide a comprehensive summary of the following document:

Document:
${text}

Summary:`;

    const messages = [
      {
        role: 'system',
        content: 'You are a helpful AI assistant that creates comprehensive summaries of documents.'
      },
      {
        role: 'user',
        content: prompt
      }
    ];
    
    const response = await callLocalLLM(messages);
    return response;
  } catch (error) {
    console.error('Document summarization error:', error);
    throw new Error('Failed to summarize document');
  }
}

export async function extractKeyPoints(text: string): Promise<string[]> {
  try {
    const prompt = `Please extract the key points from the following document. Return them as a numbered list:

Document:
${text}

Key Points:`;

    const messages = [
      {
        role: 'system',
        content: 'You are a helpful AI assistant that extracts key points from documents.'
      },
      {
        role: 'user',
        content: prompt
      }
    ];
    
    const response = await callLocalLLM(messages);
    
    // Parse the response into an array of key points
    const keyPoints = response
      .split('\n')
      .filter(line => line.trim().length > 0)
      .map(line => line.replace(/^\d+\.\s*/, '').trim())
      .filter(point => point.length > 0);
    
    return keyPoints;
  } catch (error) {
    console.error('Key points extraction error:', error);
    throw new Error('Failed to extract key points');
  }
}
