"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"

export default function FarmersPage() {
  const [user, setUser] = useState<any>(null)
  const [farmers, setFarmers] = useState<any[]>([])
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
    loadFarmers()
  }, [router])

  const loadFarmers = async () => {
    try {
      const { data, error } = await supabase
        .from("farmers")
        .select("*")
        .order("id", { ascending: false })

      if (error) {
        setError(error.message)
        setFarmers([])
      } else {
        setFarmers(data || [])
      }
    } catch (err: any) {
      setError(err.message || "Failed to load farmers")
      setFarmers([])
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
            <Link href="/dashboard/view-stock" className="block px-4 py-2.5 rounded hover:bg-green-800">View Stock</Link>
            <Link href="/dashboard/issue" className="block px-4 py-2.5 rounded hover:bg-green-800">Issue to Farmer</Link>
            <Link href="/dashboard/farmers" className="block px-4 py-2.5 rounded bg-green-700">Farmers List</Link>
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
          <h1 className="text-3xl font-bold text-[#1b4332] mb-2">Farmers List</h1>
          <p className="text-gray-600 mb-6">All issuance records</p>

          {error && (
            <div className="mb-4 bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
              Error: {error}
            </div>
          )}

          <div className="bg-white rounded-xl shadow overflow-x-auto">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading farmers...</div>
            ) : farmers.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No farmer records found.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-[#1b4332] text-white">
                  <tr>
                    <th className="text-left px-4 py-3 font-semibold">Receipt No</th>
                    <th className="text-left px-4 py-3 font-semibold">Date</th>
                    <th className="text-left px-4 py-3 font-semibold">Farmer Name</th>
                    <th className="text-left px-4 py-3 font-semibold">ID Number</th>
                    <th className="text-left px-4 py-3 font-semibold">Product</th>
                    <th className="text-right px-4 py-3 font-semibold">Qty</th>
                    <th className="text-left px-4 py-3 font-semibold">Issued By</th>
                  </tr>
                </thead>
                <tbody className="text-gray-900">
                  {farmers.map((f) => (
                    <tr key={f.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{f.receipt_no}</td>
                      <td className="px-4 py-3">{f.date}</td>
                      <td className="px-4 py-3 font-medium">{f.farmer_name}</td>
                      <td className="px-4 py-3">{f.id_number}</td>
                      <td className="px-4 py-3">{f.product}</td>
                      <td className="px-4 py-3 text-right font-bold">{f.quantity}</td>
                      <td className="px-4 py-3">{f.issued_by}</td>
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