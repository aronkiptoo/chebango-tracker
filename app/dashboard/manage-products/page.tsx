"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { createClient } from "@/lib/supabase/client"

export default function ManageProductsPage() {
  const [user, setUser] = useState<any>(null)
  const [unlocked, setUnlocked] = useState(false)
  const [adminPassword, setAdminPassword] = useState("")
  const [stock, setStock] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  // Add product
  const [newProductName, setNewProductName] = useState("")
  const [openingQty, setOpeningQty] = useState(0)

  // Receive stock
  const [receiveProduct, setReceiveProduct] = useState("")
  const [receiveQty, setReceiveQty] = useState(1)

  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const savedUser = localStorage.getItem("user")
    if (!savedUser) {
      router.push("/")
      return
    }
    const parsed = JSON.parse(savedUser)
    setUser(parsed)

    // Only allow admin
    if (parsed.mobile !== "254769468742") {
      router.push("/dashboard")
      return
    }

    loadStock()
  }, [router])

  const loadStock = async () => {
    const { data } = await supabase.from("stock").select("*").order("product")
    setStock(data || [])
    setLoading(false)
  }

  const handleUnlock = () => {
    if (adminPassword === "Changeme@123") {
      setUnlocked(true)
      setError("")
    } else {
      setError("Incorrect admin password")
    }
  }

  const handleAddProduct = async () => {
    if (!newProductName.trim()) {
      setError("Please enter a product name")
      return
    }

    setError("")
    setMessage("")

    try {
      await supabase.from("products").insert({ name: newProductName.trim() })

      await supabase.from("stock").upsert({
        product: newProductName.trim(),
        received: openingQty,
        issued: 0,
        available: openingQty,
      })

      setMessage(`Product "${newProductName}" added successfully!`)
      setNewProductName("")
      setOpeningQty(0)
      loadStock()
    } catch (err: any) {
      setError(err.message || "Failed to add product")
    }
  }

  const handleReceiveStock = async () => {
    if (!receiveProduct || receiveQty < 1) {
      setError("Please select a product and enter quantity")
      return
    }

    setError("")
    setMessage("")

    try {
      const item = stock.find((s) => s.product === receiveProduct)
      if (!item) return

      const newReceived = (item.received || 0) + receiveQty
      const newAvailable = newReceived - (item.issued || 0)

      await supabase.from("stock").upsert({
        product: receiveProduct,
        received: newReceived,
        issued: item.issued || 0,
        available: newAvailable,
      })

      setMessage(`Successfully received ${receiveQty} of ${receiveProduct}`)
      setReceiveQty(1)
      loadStock()
    } catch (err: any) {
      setError(err.message || "Failed to receive stock")
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
            <Link href="/dashboard/farmers" className="block px-4 py-2.5 rounded hover:bg-green-800">Farmers List</Link>
            <Link href="/dashboard/reports" className="block px-4 py-2.5 rounded hover:bg-green-800">Reports</Link>
            <Link href="/dashboard/manage-products" className="block px-4 py-2.5 rounded bg-green-700">Manage Products</Link>
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
          <h1 className="text-3xl font-bold text-[#1b4332] mb-2">Manage Products</h1>
          <p className="text-gray-600 mb-6">Admin only — add products and manage stock</p>

          {!unlocked ? (
            <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md border border-gray-100">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-[#1b4332]">Admin Access Required</h2>
                <p className="text-gray-600 mt-1 text-sm">
                  Enter the admin password to unlock this page.
                </p>
              </div>

              <input
                type="password"
                value={adminPassword}
                onChange={(e) => setAdminPassword(e.target.value)}
                placeholder="Enter admin password"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl mb-4 focus:ring-2 focus:ring-green-600 focus:border-green-600 outline-none text-gray-900"
              />

              {error && (
                <p className="text-red-600 text-sm mb-4 font-medium">{error}</p>
              )}

              <button
                onClick={handleUnlock}
                className="w-full py-3.5 bg-[#1b4332] text-white rounded-xl font-semibold hover:bg-[#2d6a4f] transition"
              >
                Unlock
              </button>
            </div>
          ) : (
            <>
              {message && (
                <div className="mb-5 bg-green-50 text-green-800 p-4 rounded-xl border border-green-200 font-medium">
                  {message}
                </div>
              )}
              {error && (
                <div className="mb-5 bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 font-medium">
                  {error}
                </div>
              )}

              {/* Current Stock Table */}
              <div className="bg-white rounded-2xl shadow overflow-hidden mb-8 border border-gray-100">
                <div className="bg-[#1b4332] text-white px-6 py-4 font-semibold text-lg">
                  Current Stock
                </div>
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-700">
                    <tr>
                      <th className="text-left px-6 py-3 font-semibold">Product</th>
                      <th className="text-right px-6 py-3 font-semibold">Received</th>
                      <th className="text-right px-6 py-3 font-semibold">Issued</th>
                      <th className="text-right px-6 py-3 font-semibold">Available</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-900">
                    {stock.map((item) => (
                      <tr key={item.product} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="px-6 py-3.5 font-medium">{item.product}</td>
                        <td className="px-6 py-3.5 text-right">{item.received}</td>
                        <td className="px-6 py-3.5 text-right">{item.issued}</td>
                        <td className="px-6 py-3.5 text-right font-bold text-green-700">
                          {item.available}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Add New Product */}
              <div className="bg-white rounded-2xl shadow p-6 mb-6 border border-gray-100">
                <h2 className="text-lg font-semibold text-[#1b4332] mb-4">Add New Product</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Product Name
                    </label>
                    <input
                      type="text"
                      value={newProductName}
                      onChange={(e) => setNewProductName(e.target.value)}
                      placeholder="e.g. Agripest Organic (2L Bottle)"
                      className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Opening Quantity
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={openingQty}
                      onChange={(e) => setOpeningQty(Number(e.target.value))}
                      className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600"
                    />
                  </div>
                </div>
                <button
                  onClick={handleAddProduct}
                  className="mt-5 px-6 py-2.5 bg-green-700 text-white rounded-xl font-semibold hover:bg-green-800 transition"
                >
                  + Add Product
                </button>
              </div>

              {/* Receive Stock */}
              <div className="bg-white rounded-2xl shadow p-6 border border-gray-100">
                <h2 className="text-lg font-semibold text-[#1b4332] mb-4">
                  Receive Stock (Existing Product)
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select Product
                    </label>
                    <select
                      value={receiveProduct}
                      onChange={(e) => setReceiveProduct(e.target.value)}
                      className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600"
                    >
                      <option value="">-- Choose product --</option>
                      {stock.map((s) => (
                        <option key={s.product} value={s.product}>
                          {s.product}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quantity Received
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={receiveQty}
                      onChange={(e) => setReceiveQty(Number(e.target.value))}
                      className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-green-600 focus:border-green-600"
                    />
                  </div>
                </div>
                <button
                  onClick={handleReceiveStock}
                  className="mt-5 px-6 py-2.5 bg-[#1b4332] text-white rounded-xl font-semibold hover:bg-[#2d6a4f] transition"
                >
                  Confirm Receive Stock
                </button>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}