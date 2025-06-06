import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle, AlertCircle, Info } from "lucide-react"

interface TestResultsProps {
  data: {
    score?: number
    issues?: Array<{
      severity: "error" | "warning" | "info"
      message: string
    }>
    recommendations?: string[]
  }
}

export default function TestResults({ data }: TestResultsProps) {
  if (!data) return null

  return (
    <div className="space-y-4 w-full">
      {data.score !== undefined && (
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">Score</h3>
          <div className="text-2xl font-bold">{data.score}/100</div>
        </div>
      )}

      {data.issues && data.issues.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-medium mb-4">Issues Found</h3>
            <ul className="space-y-3">
              {data.issues.map((issue, index) => (
                <li key={index} className="flex gap-2">
                  {issue.severity === "error" ? (
                    <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
                  ) : issue.severity === "warning" ? (
                    <AlertCircle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
                  ) : (
                    <Info className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
                  )}
                  <span>{issue.message}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {data.recommendations && data.recommendations.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-medium mb-4">Recommendations</h3>
            <ul className="space-y-3">
              {data.recommendations.map((recommendation, index) => (
                <li key={index} className="flex gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                  <span>{recommendation}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
