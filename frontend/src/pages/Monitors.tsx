import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Plus } from 'lucide-react'

export default function Monitors() {
  const { data: monitors, isLoading } = useQuery({
    queryKey: ['monitors'],
    queryFn: async () => {
      const response = await axios.get('/monitors/')
      return response.data.results || response.data
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Monitors</h1>
        <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
          <Plus className="mr-2 h-4 w-4" />
          Add Monitor
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {monitors?.map((monitor: any) => (
            <li key={monitor.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <span className={`h-3 w-3 rounded-full ${monitor.is_active ? 'bg-green-400' : 'bg-gray-400'}`} />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{monitor.name}</div>
                      <div className="text-sm text-gray-500">{monitor.target} ({monitor.check_type})</div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {monitor.is_paused ? 'Paused' : 'Active'}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
