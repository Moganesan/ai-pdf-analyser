// Simple local embeddings using text hashing
export class LocalEmbeddings {
  async embedDocuments(texts: string[]): Promise<number[][]> {
    return texts.map(text => this.createEmbedding(text));
  }

  async embedQuery(text: string): Promise<number[]> {
    return this.createEmbedding(text);
  }

  private createEmbedding(text: string): number[] {
    const hash = this.simpleHash(text);
    const embedding = new Array(384).fill(0);
    
    // Convert hash to embedding-like vector
    for (let i = 0; i < Math.min(hash.length, 384); i++) {
      embedding[i] = (hash.charCodeAt(i % hash.length) - 128) / 128;
    }
    
    return embedding;
  }

  private simpleHash(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  }
}
