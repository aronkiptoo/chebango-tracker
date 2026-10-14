"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"

export default function LoginPage() {
  const [mobile, setMobile] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()
  const supabase = createClient()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    const cleanMobile = mobile.trim()

    try {
      // First check if the mobile exists
      const { data: user, error: fetchError } = await supabase
        .from("users")
        .select("*")
        .eq("mobile", cleanMobile)
        .maybeSingle()

      if (fetchError) {
        console.error(fetchError)
       setError(`Database error: ${fetchError.message}`)
       setLoading(false)
       return
       }

      if (!user) {
        setError("Mobile number not found")
        setLoading(false)
        return
      }

      if (user.password !== password) {
        setError("Wrong password")
        setLoading(false)
        return
      }

      // Login successful
      localStorage.setItem("user", JSON.stringify(user))
      router.push("/dashboard")
    } catch (err) {
      console.error(err)
      setError("Something went wrong. Please try again.")
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#1b4332] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#1b4332]">Chebango Tracker</h1>
          <p className="text-gray-600 mt-2">Product Issuance & Stock System</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-black mb-1">
              Mobile number
            </label>
            <input
              type="text"
              value={mobile}
              onChange={(e) => setMobile(e.target.value)}
              placeholder="2547XXXXXXXX"
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg text-black focus:ring-2 focus:ring-[#2d6a4f] focus:border-[#2d6a4f] outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-black mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg text-black focus:ring-2 focus:ring-[#2d6a4f] focus:border-[#2d6a4f] outline-none"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg border border-red-200">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#1b4332] text-white py-3.5 rounded-lg font-bold text-lg hover:bg-[#2d6a4f] transition disabled:opacity-60"
          >
            {loading ? "Signing in..." : "SIGN IN"}
          </button>
        </form>

        <div className="mt-6 text-sm text-gray-700 bg-gray-50 p-4 rounded-lg border">
          <p className="font-semibold mb-2 text-black">Default Password = 1234</p>
          <p>• Caroline Cherotich → 254701593581</p>
          <p>• Too Patrick → 254724334842</p>
          <p>• Aron Yegon → 254769468742</p>
        </div>
      </div>
    </div>
  )
}