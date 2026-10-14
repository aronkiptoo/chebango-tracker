"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    const savedUser = localStorage.getItem("user")
    if (!savedUser) {
      router.push("/")
      return
    }
    setUser(JSON.parse(savedUser))
  }, [router])

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

  const isAdmin = user.mobile === "254769468742"

  const menuItems = [
    { name: "Home", href: "/dashboard" },
    { name: "Receive Stock", href: "/dashboard/receive-stock" },
    { name: "View Stock", href: "/dashboard/view-stock" },
    { name: "Issue to Farmer", href: "/dashboard/issue" },
    { name: "Farmers List", href: "/dashboard/farmers" },
    { name: "Reports", href: "/dashboard/reports" },
  ]

  if (isAdmin) {
    menuItems.push({ name: "Manage Products", href: "/dashboard/manage-products" })
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
            {menuItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="block w-full text-left px-4 py-2.5 rounded hover:bg-green-800 transition"
              >
                {item.name}
              </Link>
            ))}
          </nav>

          <button
            onClick={handleLogout}
            className="mt-6 w-full px-4 py-2.5 bg-red-600 rounded hover:bg-red-700 transition"
          >
            Logout
          </button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <h1 className="text-3xl font-bold text-[#1b4332] mb-2">
            Welcome, {user.name}
          </h1>
          <p className="text-gray-600 mb-8">
            Department: {user.department}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl shadow">
              <p className="text-gray-500 text-sm">Products</p>
              <p className="text-3xl font-bold text-[#1b4332] mt-1">—</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow">
              <p className="text-gray-500 text-sm">Total Available</p>
              <p className="text-3xl font-bold text-[#1b4332] mt-1">—</p>
            </div>
            <div className="bg-white p-6 rounded-xl shadow">
              <p className="text-gray-500 text-sm">Department</p>
              <p className="text-3xl font-bold text-[#1b4332] mt-1">{user.department}</p>
            </div>
          </div>

          <div className="mt-10 bg-white p-6 rounded-xl shadow">
            <h2 className="text-xl font-semibold mb-3 text-[#1b4332]">
              Quick Actions
            </h2>
            <p className="text-gray-600">
              Use the menu on the left to navigate. We will now build each page one by one.
            </p>
          </div>
        </main>
      </div>
    </div>
  )
}