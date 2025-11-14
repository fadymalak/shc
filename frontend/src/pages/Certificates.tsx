import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export default function Certificates() {
  const { data: certificates, isLoading } = useQuery({
    queryKey: ['certificates'],
    queryFn: async () => {
      const response = await axios.get('/certificates/')
      return response.data.results || response.data
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Certificates</h1>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {certificates?.map((cert: any) => (
            <li key={cert.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{cert.domain}</div>
                    <div className="text-sm text-gray-500">
                      Expires: {new Date(cert.valid_until).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      {cert.days_until_expiry} days remaining
                    </div>
                  </div>
                  {cert.is_expiring_soon && (
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                      Expiring Soon
                    </span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
