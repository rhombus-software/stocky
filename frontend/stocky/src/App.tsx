import { useState } from 'react'
import './App.css'
import { useIndicesGrid } from './hooks/getIndicesGrid'

function App() {
  const [searchTerm, setSearchTerm] = useState('')
  const { data, error, isLoading } = useIndicesGrid(searchTerm)

  return (
    <div className="min-h-screen bg-slate-950 px-2 py-4 text-slate-100 sm:px-3 sm:py-6">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:gap-4">
        <header className="flex flex-col gap-1">
          <p className="text-[10px] uppercase tracking-[0.3em] text-slate-400 sm:text-xs">Market overview</p>
        </header>

        <label className="flex flex-col gap-1.5 rounded-xl border border-slate-800 bg-slate-900/80 p-3 shadow-sm sm:p-4">
          <span className="text-xs font-medium text-slate-300 sm:text-sm">Search indices</span>
          <input
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Search by index name"
            className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-sm text-slate-100 outline-none ring-0"
          />
        </label>

        {isLoading ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 text-center text-sm text-slate-300 sm:p-8">
            Loading market indices...
          </div>
        ) : error ? (
          <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-300 sm:p-6">
            {error}
          </div>
        ) : data.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 text-center text-sm text-slate-400 sm:p-8">
            No indices match your search.
          </div>
        ) : (
          <div className="grid gap-2 grid-cols-3">
            {data.map((item) => {
              const change = Number(item.percChange ?? 0)
              const isPositive = change >= 0
              const changeLabel = `${isPositive ? '+' : ''}${change.toFixed(2)}%`

              return (
                <article
                  key={item.indexName}
                  className={`w-full rounded-xl border p-1.5 shadow-sm sm:p-3 ${isPositive
                      ? 'border-emerald-500/40 bg-emerald-500/10'
                      : 'border-rose-500/40 bg-rose-500/10'
                    }`}
                >
                  <div className="flex flex-col gap-1.5 items-center justify-between">
                  <p className="overflow-hidden w-[80%] text-ellipsis whitespace-nowrap text-sm font-semibold text-slate-50">
                    {item.indexName}
                  </p>

                  <p className="mt-3 font-semibold text-white text-xs">
                    {Number(item.last ?? 0).toLocaleString('en-IN', {
                      maximumFractionDigits: 2,
                    })}
                  </p>
                  <p
                    className={`rounded-full px-1 py-0.5 text-[10px] font-semibold sm:px-2.5 sm:text-xs ${isPositive ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                      }`}
                  >
                    {changeLabel}
                  </p>
</div>
                </article>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
