"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"

export default function ReportsPage() {
  const [user, setUser] = useState<any>(null)
  const [stock, setStock] = useState<any[]>([])
  const [farmers, setFarmers] = useState<any[]>([])
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
    loadData()
  }, [router])

  const loadData = async () => {
    const [stockRes, farmersRes] = await Promise.all([
      supabase.from("stock").select("*").order("product"),
      supabase.from("farmers").select("*")
    ])
    setStock(stockRes.data || [])
    setFarmers(farmersRes.data || [])
    setLoading(false)
  }

  const handleLogout = () => {
    localStorage.removeItem("user")
    router.push("/")
  }

  if (!user) {
    return <div className="min-h-screen bg-[#1b4332] flex items-center justify-center text-white">Loading...</div>
  }

  const totalIssued = farmers.reduce((sum, f) => sum + (Number(f.quantity) || 0), 0)
  const uniqueReceipts = new Set(farmers.map(f => f.receipt_no)).size

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
            <Link href="/dashboard/receive-stock" className="block px-4 py-2.5 rounded hover:bg-green-800">Receive Stock</Link>
            <Link href="/dashboard/view-stock" className="block px-4 py-2.5 rounded hover:bg-green-800">View Stock</Link>
            <Link href="/dashboard/issue" className="block px-4 py-2.5 rounded hover:bg-green-800">Issue to Farmer</Link>
            <Link href="/dashboard/farmers" className="block px-4 py-2.5 rounded hover:bg-green-800">Farmers List</Link>
            <Link href="/dashboard/reports" className="block px-4 py-2.5 rounded bg-green-700">Reports</Link>
          </nav>
          <button onClick={handleLogout} className="mt-6 w-full px-4 py-2.5 bg-red-600 rounded hover:bg-red-700">Logout</button>
        </aside>

        <main className="flex-1 p-8">
          <h1 className="text-3xl font-bold text-[#1b4332] mb-6">Reports</h1>

          {loading ? (
            <div className="text-gray-500">Loading reports...</div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-xl shadow">
                  <p className="text-gray-500 text-sm">Total Receipts</p>
                  <p className="text-3xl font-bold text-[#1b4332]">{uniqueReceipts}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow">
                  <p className="text-gray-500 text-sm">Total Line Items</p>
                  <p className="text-3xl font-bold text-[#1b4332]">{farmers.length}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow">
                  <p className="text-gray-500 text-sm">Total Quantity Issued</p>
                  <p className="text-3xl font-bold text-[#1b4332]">{totalIssued}</p>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow p-6">
                <h2 className="text-xl font-semibold text-[#1b4332] mb-4">Stock Summary</h2>
                <div className="space-y-3">
                  {stock.map((item) => (
                    <div key={item.product} className="flex justify-between border-b pb-2">
                      <span className="font-medium text-gray-900">{item.product}</span>
                      <span className="text-gray-700">
                        Received: <b>{item.received}</b> | Issued: <b>{item.issued}</b> | Available: <b className="text-green-700">{item.available}</b>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}