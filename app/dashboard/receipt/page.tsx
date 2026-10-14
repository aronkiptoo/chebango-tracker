"use client"
export const dynamic = 'force-dynamic'
import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"

export default function ReceiptPage() {
  const [user, setUser] = useState<any>(null)
  const [receiptData, setReceiptData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const searchParams = useSearchParams()
  const receiptNo = searchParams.get("receipt")
  const supabase = createClient()

  useEffect(() => {
    const savedUser = localStorage.getItem("user")
    if (!savedUser) {
      router.push("/")
      return
    }
    setUser(JSON.parse(savedUser))

    if (receiptNo) {
      loadReceipt(receiptNo)
    } else {
      setLoading(false)
    }
  }, [router, receiptNo])

  const loadReceipt = async (no: string) => {
    const { data } = await supabase
      .from("farmers")
      .select("*")
      .eq("receipt_no", no)
      .order("id")

    setReceiptData(data || [])
    setLoading(false)
  }

  const handlePrint = () => {
    window.print()
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

  const first = receiptData[0]
  const totalQty = receiptData.reduce((sum, item) => sum + (item.quantity || 0), 0)

  return (
    <div className="min-h-screen bg-[#f4f1e8]">
      <div className="flex">
        {/* Sidebar - hidden when printing */}
        <aside className="w-64 min-h-screen bg-[#1b4332] text-white p-6 flex flex-col print:hidden">
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
            <Link href="/dashboard/reports" className="block px-4 py-2.5 rounded hover:bg-green-800">Reports</Link>
            <Link href="/dashboard/manage-products" className="block px-4 py-2.5 rounded hover:bg-green-800">Manage Products</Link>
          </nav>
          <button onClick={handleLogout} className="mt-6 w-full px-4 py-2.5 bg-red-600 rounded hover:bg-red-700">
            Logout
          </button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="flex justify-between items-center mb-6 print:hidden">
            <div>
              <h1 className="text-3xl font-bold text-[#1b4332]">Receipt</h1>
              <p className="text-gray-600">View and print farmer receipt</p>
            </div>
            {receiptData.length > 0 && (
              <button
                onClick={handlePrint}
                className="px-6 py-3 bg-green-700 text-white rounded-xl font-semibold hover:bg-green-800"
              >
                Print / Download PDF
              </button>
            )}
          </div>

          {loading ? (
            <div className="text-gray-500">Loading receipt...</div>
          ) : !receiptNo || receiptData.length === 0 ? (
            <div className="bg-white rounded-xl shadow p-8 text-center text-gray-500">
              No receipt selected. Please issue products first.
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-lg p-8 max-w-3xl mx-auto print:shadow-none print:p-4">
              {/* Header */}
              <div className="text-center border-b-2 border-green-700 pb-4 mb-6">
                <h2 className="text-xl font-bold text-[#1b4332]">
                  MINISTRY OF AGRICULTURE - PRODUCT DISTRIBUTION PROGRAM
                </h2>
                <p className="text-lg font-semibold mt-1">CHEBANGO TEA FACTORY</p>
                <p className="text-sm text-gray-600 mt-1">Official Receipt</p>
              </div>

              {/* Receipt Info */}
              <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
                <div>
                  <p><span className="font-semibold">Receipt No:</span> {first.receipt_no}</p>
                  <p><span className="font-semibold">Date:</span> {first.date}</p>
                  <p><span className="font-semibold">Time:</span> {first.time}</p>
                </div>
                <div className="text-right">
                  <p><span className="font-semibold">Issued By:</span> {first.issued_by}</p>
                  <p><span className="font-semibold">Department:</span> {first.department}</p>
                </div>
              </div>

              {/* Farmer Details */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-[#1b4332] mb-2">Farmer Details</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <p><span className="font-medium">Name:</span> {first.farmer_name}</p>
                  <p><span className="font-medium">ID Number:</span> {first.id_number}</p>
                  <p><span className="font-medium">Grower No:</span> {first.grower_number}</p>
                  <p><span className="font-medium">Mobile:</span> {first.mobile}</p>
                </div>
              </div>

              {/* Products Table */}
              <table className="w-full text-sm mb-6">
                <thead className="bg-[#1b4332] text-white">
                  <tr>
                    <th className="text-left px-4 py-2">Product</th>
                    <th className="text-right px-4 py-2">Quantity</th>
                  </tr>
                </thead>
                <tbody>
                  {receiptData.map((item, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="px-4 py-2">{item.product}</td>
                      <td className="px-4 py-2 text-right font-bold">{item.quantity}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-100 font-bold">
                    <td className="px-4 py-2">Total Quantity</td>
                    <td className="px-4 py-2 text-right">{totalQty}</td>
                  </tr>
                </tfoot>
              </table>

              {/* Signature Area */}
              <div className="grid grid-cols-2 gap-8 mt-10 text-sm">
                <div className="border-t border-gray-400 pt-2 text-center">
                  Farmer / Recipient Signature
                </div>
                <div className="border-t border-gray-400 pt-2 text-center">
                  Authorized Officer Signature
                </div>
              </div>

              <p className="text-center text-xs text-gray-500 mt-8">
                This receipt number is traceable and secured. Keep a copy for your records.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
