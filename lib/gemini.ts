import { GoogleGenerativeAI } from '@google/generative-ai'
import { MODEL_CONFIG } from './config'

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!)

export async function callGemini(params: {
  systemPrompt: string
  userPrompt: string
  temperature: number
}): Promise<string> {
  const model = genAI.getGenerativeModel({
    model: MODEL_CONFIG.model,
    systemInstruction: params.systemPrompt,
    generationConfig: {
      responseMimeType: 'application/json',
      temperature: params.temperature,
      maxOutputTokens: MODEL_CONFIG.maxOutputTokens,
    },
  })

  const result = await model.generateContent(params.userPrompt)
  const response = result.response

  if (!response || !response.candidates || response.candidates.length === 0) {
    throw new Error('Gemini API returned no candidates')
  }

  const text = response.candidates[0].content?.parts?.[0]?.text
  if (!text) {
    throw new Error('Gemini API returned empty text in first candidate')
  }

  return text
}

export async function callGeminiWithRetry(
  params: Parameters<typeof callGemini>[0],
  retries = 2
): Promise<string> {
  let lastError: Error | unknown
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await callGemini(params)
    } catch (err) {
      lastError = err
      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
      }
    }
  }
  throw lastError
}
