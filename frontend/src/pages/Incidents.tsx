import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export default function Incidents() {
  const { data: incidents, isLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: async () => {
      const response = await axios.get('/incidents/')
      return response.data.results || response.data
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Incidents</h1>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {incidents?.map((incident: any) => (
            <li key={incident.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {incident.monitor_name} - {incident.incident_type}
                    </div>
                    <div className="text-sm text-gray-500">
                      Started: {new Date(incident.started_at).toLocaleString()}
                    </div>
                    {incident.error_message && (
                      <div className="text-sm text-red-600 mt-1">{incident.error_message}</div>
                    )}
                  </div>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    incident.status === 'open' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                  }`}>
                    {incident.status}
                  </span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
