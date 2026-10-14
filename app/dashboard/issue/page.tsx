"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"

export default function IssuePage() {
  const [user, setUser] = useState<any>(null)
  const [stock, setStock] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  const [farmerName, setFarmerName] = useState("")
  const [growerNumber, setGrowerNumber] = useState("")
  const [idNumber, setIdNumber] = useState("")
  const [mobile, setMobile] = useState("")

  const [selectedProduct, setSelectedProduct] = useState("")
  const [quantity, setQuantity] = useState(1)
  const [issueItems, setIssueItems] = useState<{ product: string; quantity: number }[]>([])

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

  const availableProducts = stock.filter((s) => (s.available || 0) > 0)

  const addProduct = () => {
    if (!selectedProduct || quantity < 1) return

    const existing = issueItems.find((i) => i.product === selectedProduct)
    if (existing) {
      setError("This product is already in the list")
      return
    }

    const stockItem = stock.find((s) => s.product === selectedProduct)
    if (!stockItem || quantity > stockItem.available) {
      setError("Not enough stock available")
      return
    }

    setIssueItems([...issueItems, { product: selectedProduct, quantity }])
    setSelectedProduct("")
    setQuantity(1)
    setError("")
  }

  const removeItem = (index: number) => {
    setIssueItems(issueItems.filter((_, i) => i !== index))
  }

  const handleIssue = async () => {
    if (!farmerName || !growerNumber || !idNumber || !mobile) {
      setError("Please fill all farmer details")
      return
    }
    if (issueItems.length === 0) {
      setError("Please add at least one product")
      return
    }

    setSaving(true)
    setError("")
    setMessage("")

    try {
      const now = new Date()
      const receiptNo = now.toISOString().slice(2, 16).replace(/[-T:]/g, "").slice(0, 12)
      const dateStr = now.toLocaleDateString("en-CA", { timeZone: "Africa/Nairobi" })
      const timeStr = now.toLocaleTimeString("en-GB", { timeZone: "Africa/Nairobi" })

      for (const item of issueItems) {
        await supabase.from("farmers").insert({
          receipt_no: receiptNo,
          date: dateStr,
          time: timeStr,
          farmer_name: farmerName,
          grower_number: growerNumber,
          id_number: idNumber,
          mobile: mobile,
          product: item.product,
          quantity: item.quantity,
          issued_by: user.name,
          department: user.department,
          issuer_mobile: user.mobile,
        })

        const stockItem = stock.find((s) => s.product === item.product)
        if (stockItem) {
          const newIssued = (stockItem.issued || 0) + item.quantity
          const newAvailable = Math.max(0, (stockItem.received || 0) - newIssued)

          await supabase.from("stock").upsert({
            product: item.product,
            received: stockItem.received || 0,
            issued: newIssued,
            available: newAvailable,
          })
        }
      }

      setMessage(`Successfully issued! Receipt No: ${receiptNo}`)
      setIssueItems([])
      setFarmerName("")
      setGrowerNumber("")
      setIdNumber("")
      setMobile("")
      loadStock()

      // Redirect to receipt page
      setTimeout(() => {
        router.push(`/dashboard/receipt?receipt=${receiptNo}`)
      }, 1200)
    } catch (err: any) {
      setError(err.message || "Failed to issue products")
    } finally {
      setSaving(false)
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
            <Link href="/dashboard/issue" className="block px-4 py-2.5 rounded bg-green-700">Issue to Farmer</Link>
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
          <h1 className="text-3xl font-bold text-[#1b4332] mb-2">Issue Product to Farmer</h1>
          <p className="text-gray-700 mb-6">Fill farmer details and select products to issue</p>

          {error && (
            <div className="mb-4 bg-red-50 text-red-700 p-4 rounded-lg border border-red-200 font-medium">
              {error}
            </div>
          )}
          {message && (
            <div className="mb-4 bg-green-50 text-green-800 p-4 rounded-lg border border-green-200 font-medium">
              {message}
            </div>
          )}

          {/* Farmer Details */}
          <div className="bg-white rounded-xl shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-[#1b4332] mb-4">Farmer Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-1">
                  Name of the Farmer *
                </label>
                <input
                  type="text"
                  value={farmerName}
                  onChange={(e) => setFarmerName(e.target.value)}
                  placeholder="Enter farmer full name"
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-600 focus:border-green-600 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-1">
                  Grower Number *
                </label>
                <input
                  type="text"
                  value={growerNumber}
                  onChange={(e) => setGrowerNumber(e.target.value)}
                  placeholder="Enter grower number"
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-600 focus:border-green-600 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-1">
                  ID Number *
                </label>
                <input
                  type="text"
                  value={idNumber}
                  onChange={(e) => setIdNumber(e.target.value)}
                  placeholder="Enter ID number"
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-600 focus:border-green-600 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-1">
                  Mobile Number *
                </label>
                <input
                  type="text"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  placeholder="Enter mobile number"
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-green-600 focus:border-green-600 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Products to Issue */}
          <div className="bg-white rounded-xl shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-[#1b4332] mb-4">Products to Issue</h2>

            {issueItems.length > 0 && (
              <div className="mb-4 space-y-2">
                {issueItems.map((item, index) => (
                  <div key={index} className="flex justify-between items-center bg-gray-50 px-4 py-2.5 rounded-lg">
                    <span className="font-medium text-gray-900">
                      {item.quantity} × {item.product}
                    </span>
                    <button
                      onClick={() => removeItem(index)}
                      className="text-red-600 hover:text-red-800 font-bold"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex flex-col md:flex-row gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-900 mb-1">
                  Select Product
                </label>
                <select
                  value={selectedProduct}
                  onChange={(e) => setSelectedProduct(e.target.value)}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-green-600 focus:border-green-600 outline-none"
                >
                  <option value="">-- Choose product --</option>
                  {availableProducts.map((p) => (
                    <option key={p.product} value={p.product}>
                      {p.product} (Available: {p.available})
                    </option>
                  ))}
                </select>
              </div>
              <div className="w-32">
                <label className="block text-sm font-semibold text-gray-900 mb-1">
                  Quantity
                </label>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-green-600 focus:border-green-600 outline-none"
                />
              </div>
              <button
                onClick={addProduct}
                className="px-6 py-2.5 bg-[#1b4332] text-white rounded-lg hover:bg-green-800 font-medium"
              >
                Add to List
              </button>
            </div>
          </div>

          <button
            onClick={handleIssue}
            disabled={saving}
            className="w-full md:w-auto px-8 py-3 bg-green-700 text-white font-bold rounded-lg hover:bg-green-800 disabled:opacity-60"
          >
            {saving ? "Issuing..." : "Issue All Products & Generate Receipt"}
          </button>
        </main>
      </div>
    </div>
  )
}