import { GoogleGenerativeAI } from '@google/generative-ai';

export const GEMINI_MODEL = 'gemini-1.5-flash'; // Change this to update everywhere

export function getGeminiClient() {
  if (!process.env.GEMINI_API_KEY) {
    throw new Error('GEMINI_API_KEY is not set in environment variables');
  }
  return new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
}

export async function generateGeminiContent(prompt: string, modelName: string = GEMINI_MODEL) {
  const genAI = getGeminiClient();
  const model = genAI.getGenerativeModel({ model: modelName });
  const result = await model.generateContent(prompt);
  return result.response.text();
} 