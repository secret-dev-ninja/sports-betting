import * as React from "react"

export function Badge({ children, variant = "default" }: { children: React.ReactNode, variant?: "default" | "secondary" }) {
  const baseClasses = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold"
  const variantClasses = variant === "secondary" ? "bg-gray-100 text-gray-800" : "bg-primary text-primary-foreground"
  
  return (
    <div className={`${baseClasses} ${variantClasses}`}>
      {children}
    </div>
  )
}