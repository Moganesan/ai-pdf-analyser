#!/bin/bash

echo "🚀 Setting up AI PDF Analyzer..."

# Clean npm cache
echo "🧹 Cleaning npm cache..."
npm cache clean --force

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads

# Create vector-store directory
echo "🗄️ Creating vector-store directory..."
mkdir -p vector-store

# Create .env.local file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "⚙️ Creating .env.local file..."
    cat > .env.local << EOF
# OpenAI API Key (for embeddings)
OPENAI_API_KEY=your_openai_api_key_here

# Local LLM Configuration (llama.cpp server)
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=dummy-key
LLM_MODEL=llama2
EOF
    echo "✅ Created .env.local file. Please update with your API keys."
fi

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env.local with your OpenAI API key"
echo "2. Start your llama.cpp server:"
echo "   ./server -m models/your-model.gguf --host 0.0.0.0 --port 11434"
echo "3. Run the development server:"
echo "   npm run dev"
echo ""
echo "🌐 Open http://localhost:3000 to see the application"
