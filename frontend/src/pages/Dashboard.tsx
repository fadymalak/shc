import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Activity, AlertCircle, TrendingUp, Shield } from 'lucide-react'

export default function Dashboard() {
  const { data: incidents } = useQuery({
    queryKey: ['incidents', 'stats'],
    queryFn: async () => {
      const response = await axios.get('/incidents/stats/')
      return response.data
    },
  })

  const { data: monitors } = useQuery({
    queryKey: ['monitors'],
    queryFn: async () => {
      const response = await axios.get('/monitors/')
      return response.data.results || response.data
    },
  })

  const { data: certificates } = useQuery({
    queryKey: ['certificates', 'expiring'],
    queryFn: async () => {
      const response = await axios.get('/certificates/expiring_soon/')
      return response.data
    },
  })

  const stats = [
    {
      name: 'Total Monitors',
      value: monitors?.length || 0,
      icon: Activity,
      color: 'text-blue-600',
    },
    {
      name: 'Open Incidents',
      value: incidents?.open || 0,
      icon: AlertCircle,
      color: 'text-red-600',
    },
    {
      name: 'Total Incidents',
      value: incidents?.total || 0,
      icon: TrendingUp,
      color: 'text-yellow-600',
    },
    {
      name: 'Expiring Certificates',
      value: certificates?.length || 0,
      icon: Shield,
      color: 'text-orange-600',
    },
  ]

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">{stat.name}</dt>
                      <dd className="text-lg font-medium text-gray-900">{stat.value}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
