import axios from "axios"
import { useMemo } from "react"
import useSWR from "swr"

type IndexItem = {
  indexName?: string
  last?: string
  percChange?: string
}

type ApiResponse = {
  data?: IndexItem[]
}

const buildUrl = () => {
  const date = Date.now()
  return `https://liveindexsa.niftyindices.com/jsonfiles/LiveIndicesWatch.json?{}&_=${date}`
}

const fetchIndicesGrid = async (url: string) => {
  const response = await axios.get<ApiResponse | string>(url)
  const data = response.data

  if (typeof data === "string") {
    return JSON.parse(data) as ApiResponse
  }

  return data
}

export const getIndicesGrid = async () => {
  const url = buildUrl()
  return fetchIndicesGrid(url)
}

export const useIndicesGrid = (searchTerm = "") => {
  const url = useMemo(() => buildUrl(), [])
  const { data, error, isLoading, mutate } = useSWR<ApiResponse | undefined>(
    [url],
    ([currentUrl]) => fetchIndicesGrid(currentUrl),
    {
      revalidateOnFocus: false,
      refreshInterval: 60000,
    },
  )

  const normalizedData = useMemo(() => {
    const items = Array.isArray(data?.data) ? data.data : []
    const query = searchTerm.trim().toLowerCase()

    return items
      .filter((item) => {
        const indexName = item.indexName?.toLowerCase() ?? ""
        return !query || indexName.includes(query)
      })
      .map((item) => ({
        ...item,
        indexName: item.indexName ?? "Unknown Index",
        last: item.last ?? "0",
        percChange: item.percChange ?? "0",
      }))
      .sort((a, b) => {
        const changeA = Number(a.percChange ?? 0)
        const changeB = Number(b.percChange ?? 0)
        return changeB - changeA
      })
  }, [data, searchTerm])

  return {
    data: normalizedData,
    isLoading,
    error,
    mutate,
  }
}