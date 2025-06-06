import { NextResponse } from "next/server"
import { generateGeminiContent, GEMINI_MODEL } from "@/app/gemini"

export async function POST(request: Request) {
  try {
    const { url, testScenario } = await request.json()

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 })
    }

    // Fetch the website content
    let websiteContent
    try {
      const response = await fetch(url)
      websiteContent = await response.text()
    } catch (error) {
      return NextResponse.json({ error: "Failed to fetch website content" }, { status: 400 })
    }

    // Extract text content and form elements from HTML
    const textContent = websiteContent
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, " ")
      .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")
      .trim()

    // Extract form elements for better analysis
    const formElements = websiteContent.match(/<form[\s\S]*?<\/form>/gi) || []
    const inputElements = websiteContent.match(/<input[^>]*>/gi) || []
    const buttonElements = websiteContent.match(/<button[^>]*>[\s\S]*?<\/button>/gi) || []

    const prompt = `
You are an expert software tester and QA automation engineer.

I will provide a set of requirements, behaviors, or user stories for a web form, input field, or feature.

For each described requirement:

1. **Identify all validation rules and intended behaviors.**
2. **Write comprehensive unit test cases** covering both:
   - Valid (should pass) scenarios  
   - Invalid (should fail or show an error) scenarios

3. For every test case, include **exactly** these fields:
   - **test_name** - short descriptive title
   - **steps_or_input** - the sequence of user actions or data entered
   - **expected_outcome** - what should happen (success, error message, etc.)
   - **reason_for_failure** - *only for negative cases*; why the input should be rejected

Return the complete test suite as a single JSON array so it can be parsed programmatically.

Website URL: ${url}
Website Content Summary: ${textContent.substring(0, 2000)}
Form Elements Found: ${formElements.length > 0 ? formElements.join("\n") : "No forms detected"}
Input Elements: ${inputElements.slice(0, 10).join("\n")}
Button Elements: ${buttonElements.slice(0, 5).join("\n")}

${testScenario ? `Specific Test Scenario: ${testScenario}` : "Generate comprehensive test cases for all interactive elements found on this webpage, focusing on forms, inputs, and user interactions."}

Generate comprehensive test cases following the exact format specified above.
    `

    // Use Gemini SDK to generate test cases
    const responseText = await generateGeminiContent(prompt, GEMINI_MODEL)

    // Parse the response
    let testCases
    try {
      testCases = JSON.parse(responseText)
    } catch (e) {
      // If JSON parsing fails, try to extract JSON from the response
      const jsonMatch = responseText.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        try {
          testCases = JSON.parse(jsonMatch[0])
        } catch (e2) {
          testCases = [
            {
              test_name: "Parsing Error",
              steps_or_input: "Could not parse LLM response",
              expected_outcome: "Manual review required",
              reason_for_failure: "Response format issue",
            },
          ]
        }
      } else {
        testCases = [
          {
            test_name: "Response Error",
            steps_or_input: "LLM did not return valid JSON",
            expected_outcome: "Retry with different input",
            reason_for_failure: "Invalid response format",
          },
        ]
      }
    }

    return NextResponse.json({
      testCases,
      websiteAnalysis: {
        formsFound: formElements.length,
        inputsFound: inputElements.length,
        buttonsFound: buttonElements.length,
        contentLength: textContent.length,
      },
    })
  } catch (error) {
    console.error("Error in test API:", error)
    return NextResponse.json({ error: "Failed to analyze website" }, { status: 500 })
  }
}
