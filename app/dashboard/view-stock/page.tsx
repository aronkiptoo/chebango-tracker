"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"

export default function ViewStockPage() {
  const [user, setUser] = useState<any>(null)
  const [stock, setStock] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
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
    try {
      const { data, error } = await supabase
        .from("stock")
        .select("*")
        .order("product")

      if (error) {
        console.error(error)
        setError(error.message)
        setStock([])
      } else {
        setStock(data || [])
      }
    } catch (err: any) {
      console.error(err)
      setError(err.message || "Failed to load stock")
      setStock([])
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("user")
    router.push("/")
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-[#1b4332] flex items-center justify-center text-white">
        Loading...
      </div>
    )
  }

  const totalAvailable = stock.reduce((sum, item) => sum + (Number(item.available) || 0), 0)

  return (
    <div className="min-h-screen bg-[#f4f1e8]">
      <div className="flex">
        {/* Sidebar */}
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
            <Link href="/dashboard/receive-stock" className="block px-4 py-2.5 rounded hover:bg-green-800">Receive Stock</Link>
            <Link href="/dashboard/view-stock" className="block px-4 py-2.5 rounded bg-green-700">View Stock</Link>
            <Link href="/dashboard/issue" className="block px-4 py-2.5 rounded hover:bg-green-800">Issue to Farmer</Link>
            <Link href="/dashboard/farmers" className="block px-4 py-2.5 rounded hover:bg-green-800">Farmers List</Link>
            <Link href="/dashboard/reports" className="block px-4 py-2.5 rounded hover:bg-green-800">Reports</Link>
            {user.mobile === "254769468742" && (
              <Link href="/dashboard/manage-products" className="block px-4 py-2.5 rounded hover:bg-green-800">Manage Products</Link>
            )}
          </nav>

          <button
            onClick={handleLogout}
            className="mt-6 w-full px-4 py-2.5 bg-red-600 rounded hover:bg-red-700"
          >
            Logout
          </button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <h1 className="text-3xl font-bold text-[#1b4332] mb-2">View Stock</h1>
          <p className="text-gray-600 mb-6">Current stock levels from the database</p>

          {error && (
            <div className="mb-4 bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
              Error: {error}
            </div>
          )}

          <div className="bg-white rounded-xl shadow overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading stock...</div>
            ) : stock.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No stock records found in the database.
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-[#1b4332] text-white">
                  <tr>
                    <th className="text-left px-6 py-3">Product</th>
                    <th className="text-right px-6 py-3">Received</th>
                    <th className="text-right px-6 py-3">Issued</th>
                    <th className="text-right px-6 py-3">Available</th>
                  </tr>
                </thead>
                <tbody>
                  {stock.map((item) => (
                    <tr key={item.product} className="border-b hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-[#1b4332]">{item.product}</td>
                      <td className="px-6 py-4 text-right">{item.received ?? 0}</td>
                      <td className="px-6 py-4 text-right">{item.issued ?? 0}</td>
                      <td className="px-6 py-4 text-right font-bold text-green-700">
                        {item.available ?? 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="mt-6 bg-white p-5 rounded-xl shadow inline-block">
            <p className="text-gray-500 text-sm">Total Available Stock</p>
            <p className="text-3xl font-bold text-[#1b4332]">
              {totalAvailable.toLocaleString()}
            </p>
          </div>
        </main>
      </div>
    </div>
  )
}