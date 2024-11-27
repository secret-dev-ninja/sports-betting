import * as React from "react"

export function Card({ children, className }: { children: React.ReactNode, className?: string }) {
  return <div className={`bg-white rounded-lg shadow ${className}`}>{children}</div>
}

export function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="p-6">{children}</div>
}

export function CardTitle({ children, className }: { children: React.ReactNode, className?: string }) {
  return <h3 className={`text-lg font-semibold ${className}`}>{children}</h3>
}

export function CardContent({ children, variant = "default" }: { children: React.ReactNode, variant?:"default" | "child" }) {
  const baseClasses = "pt-0";
  const variantClasses = variant === "child" ? 'p-6' : ''; 

  return <div className={`${baseClasses} ${variantClasses}`}>{children}</div>
}