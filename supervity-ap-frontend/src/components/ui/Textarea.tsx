import * as React from "react"
import { cn } from "@/lib/utils"

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-gray-light bg-transparent px-3 py-2 text-sm placeholder:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-primary disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea } 