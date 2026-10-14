export type User = {
  mobile: string
  name: string
  department: string
  password: string
  must_change_password?: boolean
}

export type Product = {
  id?: number
  name: string
  created_at?: string
}

export type Stock = {
  product: string
  received: number
  issued: number
  available: number
}

export type Farmer = {
  id?: number
  receipt_no: string
  date: string
  time: string
  farmer_name: string
  grower_number: string
  id_number: string
  mobile: string
  product: string
  quantity: number
  issued_by: string
  department: string
  issuer_mobile: string
}