"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"

export default function ReceiveStockPage() {
  const [user, setUser] = useState<any>(null)
  const [stock, setStock] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const savedUser = localStorage.getItem("user")
    if (!savedUser) {
      router.push("/")
      return
    }
    setUser(JSON.parse(savedUser))
    loadStock()
  }, [router])

  const loadStock = async () => {
    const { data } = await supabase.from("stock").select("*").order("product")
    setStock(data || [])
    setLoading(false)
  }

  const handleLogout = () => {
    localStorage.removeItem("user")
    router.push("/")
  }

  if (!user) {
    return <div className="min-h-screen bg-[#1b4332] flex items-center justify-center text-white">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-[#f4f1e8]">
      <div className="flex">
        <aside className="w-64 min-h-screen bg-[#1b4332] text-white p-6 flex flex-col">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-green-400">Chebango</h2>
            <p className="text-sm text-gray-300">Tracker System</p>
          </div>
          <div className="mb-6">
            <p className="font-semibold">{user.name}</p>
            <p className="text-sm text-gray-300">{user.department}</p>
            <p className="text-sm text-gray-400">{user.mobile}</p>
          </div>
          <nav className="space-y-2 flex-1">
            <Link href="/dashboard" className="block px-4 py-2.5 rounded hover:bg-green-800">Home</Link>
            <Link href="/dashboard/receive-stock" className="block px-4 py-2.5 rounded bg-green-700">Receive Stock</Link>
            <Link href="/dashboard/view-stock" className="block px-4 py-2.5 rounded hover:bg-green-800">View Stock</Link>
            <Link href="/dashboard/issue" className="block px-4 py-2.5 rounded hover:bg-green-800">Issue to Farmer</Link>
            <Link href="/dashboard/farmers" className="block px-4 py-2.5 rounded hover:bg-green-800">Farmers List</Link>
            <Link href="/dashboard/reports" className="block px-4 py-2.5 rounded hover:bg-green-800">Reports</Link>
          </nav>
          <button onClick={handleLogout} className="mt-6 w-full px-4 py-2.5 bg-red-600 rounded hover:bg-red-700">Logout</button>
        </aside>

        <main className="flex-1 p-8">
          <h1 className="text-3xl font-bold text-[#1b4332] mb-2">Receive Stock</h1>
          <p className="text-gray-600 mb-6">View current stock. New stock is added by Admin under Manage Products.</p>

          <div className="bg-white rounded-xl shadow overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading...</div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-[#1b4332] text-white">
                  <tr>
                    <th className="text-left px-6 py-3">Product</th>
                    <th className="text-right px-6 py-3">Received</th>
                    <th className="text-right px-6 py-3">Issued</th>
                    <th className="text-right px-6 py-3">Available</th>
                  </tr>
                </thead>
                <tbody className="text-gray-900">
                  {stock.map((item) => (
                    <tr key={item.product} className="border-b hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium">{item.product}</td>
                      <td className="px-6 py-4 text-right">{item.received}</td>
                      <td className="px-6 py-4 text-right">{item.issued}</td>
                      <td className="px-6 py-4 text-right font-bold text-green-700">{item.available}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}