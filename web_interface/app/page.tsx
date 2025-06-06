"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Globe,
  Play,
  BarChart3,
  CheckCircle,
  Clock,
  Settings,
  Download,
  AlertCircle,
  ArrowDown,
  Zap,
  Sparkles,
  Rocket,
  Code,
  TestTube,
} from "lucide-react"

export default function SAILDashboard() {
  const [url, setUrl] = useState("")
  const [testPrompt, setTestPrompt] = useState("")
  const [loading, setLoading] = useState(false)
  const [testResults, setTestResults] = useState<any>(null)
  const [error, setError] = useState("")
  const [showBreakdown, setShowBreakdown] = useState(false)

  const runTest = async () => {
    if (!url || !testPrompt) return

    setLoading(true)
    setError("")
    setShowBreakdown(false)

    try {
      // Show breakdown animation
      setTimeout(() => setShowBreakdown(true), 1000)

      const response = await fetch("/api/sail/run-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, testPrompt }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate test cases")
      }

      setTestResults(data)
    } catch (error: any) {
      console.error("Test execution failed:", error)
      setError(error.message || "Failed to generate test cases")
      setShowBreakdown(false)
    } finally {
      setLoading(false)
    }
  }

  const downloadTestCases = () => {
    if (!testResults) return

    const dataStr = JSON.stringify(testResults, null, 2)
    const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(dataStr)

    const exportFileDefaultName = `sail_test_cases_${new Date().toISOString().split("T")[0]}.json`

    const linkElement = document.createElement("a")
    linkElement.setAttribute("href", dataUri)
    linkElement.setAttribute("download", exportFileDefaultName)
    linkElement.click()
  }

  // Mock data for demonstration
  const mockStats = {
    totalTests: testResults?.testCases?.length || 0,
    completed: testResults ? 1 : 0,
    averageScore: testResults?.score || 0,
    running: loading ? 1 : 0,
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-950 to-gray-900">
      {/* Header with gradient background */}
      <header className="bg-gradient-to-r from-gray-900 to-gray-800 border-b border-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center backdrop-blur-sm animate-float">
                <Rocket className="w-7 h-7 text-emerald-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold gradient-text">
                  SAIL Testing Agent
                </h1>
                <p className="text-gray-400">Smart Automation for Intelligent LLM-powered Testing</p>
              </div>
            </div>
            <nav className="flex items-center space-x-6">
              <Button variant="ghost" className="text-gray-400 hover:text-emerald-400 hover:bg-gray-800/50">
                <Settings className="w-5 h-5 mr-2" />
                Settings
              </Button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Quick Test Section with enhanced styling */}
        <Card className="mb-8 border-0 shadow-xl bg-gray-800/50 backdrop-blur-sm card-hover">
          <CardHeader className="border-b border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-violet-500 rounded-lg flex items-center justify-center">
                <TestTube className="w-6 h-6 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl font-bold gradient-text">
                  Quick Test
                </CardTitle>
                <CardDescription className="text-gray-400">
                  Enter a URL and describe what you want to test. SAIL will generate comprehensive unit test cases.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 flex items-center">
                <Globe className="w-4 h-4 mr-2 text-emerald-400" />
                Website URL
              </label>
              <Input
                placeholder="https://example.com or file:///path/to/your/html/file.html"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="input-focus"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-300 flex items-center">
                <Code className="w-4 h-4 mr-2 text-violet-400" />
                Test Description
              </label>
              <Textarea
                placeholder="I want to test the login functionality with valid and invalid credentials"
                value={testPrompt}
                onChange={(e) => setTestPrompt(e.target.value)}
                rows={4}
                className="input-focus"
              />
              <p className="text-xs text-gray-500 flex items-center">
                <Sparkles className="w-3 h-3 mr-1 text-emerald-400" />
                Describe what you want to test in natural language. SAIL will break it into detailed unit test cases.
              </p>
            </div>

            {error && (
              <div className="flex items-center space-x-2 text-red-400 bg-red-900/20 p-4 rounded-lg border border-red-900/50">
                <AlertCircle className="w-5 h-5" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <div className="flex justify-end">
              <Button
                onClick={runTest}
                disabled={loading || !url || !testPrompt}
                className="button-gradient px-6 py-2 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300"
              >
                {loading ? (
                  <>
                    <Clock className="w-5 h-5 mr-2 animate-spin" />
                    Generating Tests...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    Generate Test Cases
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results Section with enhanced animations */}
        {(loading || showBreakdown || testResults) && (
          <Card className="mb-8 border-0 shadow-xl bg-gray-800/50 backdrop-blur-sm card-hover">
            <CardHeader className="border-b border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-emerald-500 rounded-lg flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-2xl font-bold gradient-text">
                    SAIL Breakdown Process
                  </CardTitle>
                  <CardDescription className="text-gray-400">
                    Watch how SAIL breaks down your test description into structured unit test cases
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-8">
              {/* Step 1: Original Input */}
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg">
                  <span className="text-lg font-bold text-white">1</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-200 mb-3">Original Test Description</h3>
                  <div className="bg-gradient-to-r from-gray-800 to-gray-900 p-4 rounded-lg border-l-4 border-emerald-500 shadow-sm">
                    <p className="text-sm text-gray-300 italic">"{testPrompt}"</p>
                  </div>
                </div>
              </div>

              {/* Arrow */}
              {(showBreakdown || testResults) && (
                <div className="flex justify-center">
                  <ArrowDown className="w-8 h-8 text-emerald-400 animate-bounce" />
                </div>
              )}

              {/* Step 2: SAIL Analysis */}
              {(showBreakdown || testResults) && (
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-violet-500 to-violet-600 rounded-lg flex items-center justify-center shadow-lg">
                    <span className="text-lg font-bold text-white">2</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-200 mb-3">SAIL Analysis</h3>
                    <div className="bg-gradient-to-r from-gray-800 to-gray-900 p-4 rounded-lg border-l-4 border-violet-500 shadow-sm">
                      {loading ? (
                        <div className="flex items-center space-x-3">
                          <Clock className="w-5 h-5 animate-spin text-violet-400" />
                          <span className="text-sm text-gray-300">
                            Analyzing test requirements and identifying validation rules...
                          </span>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <p className="text-sm text-gray-300 flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2 text-emerald-400" />
                            Identified validation rules and behaviors
                          </p>
                          <p className="text-sm text-gray-300 flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2 text-emerald-400" />
                            Generated positive and negative test scenarios
                          </p>
                          <p className="text-sm text-gray-300 flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2 text-emerald-400" />
                            Created Testing Agent compatible actions
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Arrow */}
              {testResults && (
                <div className="flex justify-center">
                  <ArrowDown className="w-8 h-8 text-violet-400" />
                </div>
              )}

              {/* Step 3: Generated Unit Tests */}
              {testResults && (
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg">
                    <span className="text-lg font-bold text-white">3</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-200 mb-3">Generated Unit Test Cases</h3>
                    <div className="bg-gradient-to-r from-gray-800 to-gray-900 p-4 rounded-lg border-l-4 border-emerald-500 shadow-sm">
                      <div className="space-y-4">
                        {testResults.testCases.map((test: any, index: number) => (
                          <div key={index} className="bg-gray-800/50 p-3 rounded-lg shadow-sm">
                            <h4 className="font-medium text-gray-200 mb-2">{test.test_name}</h4>
                            <div className="space-y-2 text-sm">
                              <p className="text-gray-300">
                                <span className="font-medium">Steps:</span> {test.steps_or_input}
                              </p>
                              <p className="text-gray-300">
                                <span className="font-medium">Expected:</span> {test.expected_outcome}
                              </p>
                              {test.reason_for_failure && (
                                <p className="text-red-400">
                                  <span className="font-medium">Failure Reason:</span> {test.reason_for_failure}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Download Button */}
              {testResults && (
                <div className="flex justify-end mt-6">
                  <Button
                    onClick={downloadTestCases}
                    className="button-gradient px-6 py-2 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download Test Cases
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Generated Tests</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-3xl font-bold">{mockStats.totalTests}</span>
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-xs text-gray-500 mt-1">Unit Test Cases</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Completed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-3xl font-bold">{mockStats.completed}</span>
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-xs text-gray-500 mt-1">Test Sessions</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Quality Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-3xl font-bold text-green-600">{mockStats.averageScore}%</span>
                <span className="text-sm text-green-600 font-medium">%</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">Test Coverage</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-3xl font-bold">{mockStats.running}</span>
                <Clock className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-xs text-gray-500 mt-1">Running</p>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Test Results Section */}
        <Card>
          <CardHeader>
            <CardTitle>Detailed Test Cases</CardTitle>
            <CardDescription>Complete breakdown of generated unit test cases</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {testResults ? (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <CheckCircle className="w-6 h-6 text-green-600" />
                      <div>
                        <p className="font-medium text-gray-900">Test Generation Complete</p>
                        <p className="text-sm text-gray-500">{testResults.websiteAnalysis?.url}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className="text-2xl font-bold text-green-600">{testResults.score}%</span>
                      <Button variant="outline" size="sm" onClick={downloadTestCases}>
                        <Download className="w-4 h-4 mr-2" />
                        Export JSON
                      </Button>
                    </div>
                  </div>

                  {/* Individual Test Cases */}
                  <div className="space-y-4">
                    {testResults.testCases?.map((testCase: any, index: number) => (
                      <div key={index} className="border rounded-lg p-6 space-y-4 bg-white shadow-sm">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                              <span className="text-sm font-semibold text-gray-600">{index + 1}</span>
                            </div>
                            <div>
                              <h3 className="font-semibold text-lg text-gray-900">{testCase.test_name}</h3>
                              <p className="text-sm text-gray-500 mt-1">Unit Test Case</p>
                            </div>
                          </div>
                          <Badge variant={testCase.reason_for_failure ? "destructive" : "default"}>
                            {testCase.reason_for_failure ? "Negative Test" : "Positive Test"}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <div>
                            <h4 className="font-medium text-sm text-gray-600 mb-3 flex items-center">
                              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                              Steps/Input
                            </h4>
                            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                              <p className="text-sm text-gray-800">{testCase.steps_or_input}</p>
                            </div>
                          </div>

                          <div>
                            <h4 className="font-medium text-sm text-gray-600 mb-3 flex items-center">
                              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                              Expected Outcome
                            </h4>
                            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                              <p className="text-sm text-gray-800">{testCase.expected_outcome}</p>
                            </div>
                          </div>
                        </div>

                        {testCase.reason_for_failure && (
                          <div>
                            <h4 className="font-medium text-sm text-gray-600 mb-3 flex items-center">
                              <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                              Reason for Failure
                            </h4>
                            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                              <p className="text-sm text-red-800">{testCase.reason_for_failure}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No test cases generated yet</h3>
                  <p className="text-gray-500">
                    Enter a URL and test description above to see SAIL break down your test into unit test cases.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
