import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useState } from 'react'
import { Plus, Bell, Mail, MessageSquare, TestTube } from 'lucide-react'

interface NotificationChannel {
  id: number
  name: string
  channel_type: 'slack' | 'teams' | 'email'
  is_active: boolean
  notify_on_downtime: boolean
  notify_on_high_latency: boolean
  notify_on_resolution: boolean
}

export default function Notifications() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    channel_type: 'email' as 'slack' | 'teams' | 'email',
    slack_webhook_url: '',
    slack_channel: '',
    teams_webhook_url: '',
    email_addresses: '',
    notify_on_downtime: true,
    notify_on_high_latency: true,
    notify_on_resolution: true,
  })

  const { data: channels, isLoading } = useQuery({
    queryKey: ['notification-channels'],
    queryFn: async () => {
      const response = await axios.get('/notifications/channels/')
      return response.data.results || response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await axios.post('/notifications/channels/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] })
      setShowForm(false)
      setFormData({
        name: '',
        channel_type: 'email',
        slack_webhook_url: '',
        slack_channel: '',
        teams_webhook_url: '',
        email_addresses: '',
        notify_on_downtime: true,
        notify_on_high_latency: true,
        notify_on_resolution: true,
      })
    },
  })

  const testMutation = useMutation({
    mutationFn: async (channelId: number) => {
      const response = await axios.post(`/notifications/channels/${channelId}/test/`)
      return response.data
    },
  })

  const toggleActiveMutation = useMutation({
    mutationFn: async ({ id, is_active }: { id: number; is_active: boolean }) => {
      const response = await axios.patch(`/notifications/channels/${id}/`, { is_active })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-channels'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  const getChannelIcon = (type: string) => {
    switch (type) {
      case 'slack':
        return <MessageSquare className="h-5 w-5" />
      case 'teams':
        return <MessageSquare className="h-5 w-5" />
      case 'email':
        return <Mail className="h-5 w-5" />
      default:
        return <Bell className="h-5 w-5" />
    }
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Notifications</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Channel
        </button>
      </div>

      {showForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Create Notification Channel</h2>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Channel Type</label>
                <select
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  value={formData.channel_type}
                  onChange={(e) => setFormData({ ...formData, channel_type: e.target.value as any })}
                >
                  <option value="email">Email</option>
                  <option value="slack">Slack</option>
                  <option value="teams">Microsoft Teams</option>
                </select>
              </div>

              {formData.channel_type === 'slack' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Slack Webhook URL</label>
                    <input
                      type="url"
                      required
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                      value={formData.slack_webhook_url}
                      onChange={(e) => setFormData({ ...formData, slack_webhook_url: e.target.value })}
                      placeholder="https://hooks.slack.com/services/..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Slack Channel (optional)</label>
                    <input
                      type="text"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                      value={formData.slack_channel}
                      onChange={(e) => setFormData({ ...formData, slack_channel: e.target.value })}
                      placeholder="#alerts"
                    />
                  </div>
                </>
              )}

              {formData.channel_type === 'teams' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Microsoft Teams Webhook URL</label>
                  <input
                    type="url"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.teams_webhook_url}
                    onChange={(e) => setFormData({ ...formData, teams_webhook_url: e.target.value })}
                    placeholder="https://outlook.office.com/webhook/..."
                  />
                </div>
              )}

              {formData.channel_type === 'email' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email Addresses</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    value={formData.email_addresses}
                    onChange={(e) => setFormData({ ...formData, email_addresses: e.target.value })}
                    placeholder="dev@example.com, ops@example.com"
                  />
                  <p className="mt-1 text-sm text-gray-500">Comma-separated list of email addresses</p>
                </div>
              )}

              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={formData.notify_on_downtime}
                    onChange={(e) => setFormData({ ...formData, notify_on_downtime: e.target.checked })}
                  />
                  <span className="ml-2 text-sm text-gray-700">Notify on Downtime</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={formData.notify_on_high_latency}
                    onChange={(e) => setFormData({ ...formData, notify_on_high_latency: e.target.checked })}
                  />
                  <span className="ml-2 text-sm text-gray-700">Notify on High Latency</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={formData.notify_on_resolution}
                    onChange={(e) => setFormData({ ...formData, notify_on_resolution: e.target.checked })}
                  />
                  <span className="ml-2 text-gray-700">Notify on Resolution</span>
                </label>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  Create Channel
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {channels?.map((channel: NotificationChannel) => (
            <li key={channel.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {getChannelIcon(channel.channel_type)}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{channel.name}</div>
                      <div className="text-sm text-gray-500 capitalize">{channel.channel_type}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {channel.notify_on_downtime && 'Downtime '}
                        {channel.notify_on_high_latency && 'High Latency '}
                        {channel.notify_on_resolution && 'Resolution'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => testMutation.mutate(channel.id)}
                      disabled={testMutation.isPending}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <TestTube className="mr-1 h-4 w-4" />
                      Test
                    </button>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={channel.is_active}
                        onChange={(e) =>
                          toggleActiveMutation.mutate({ id: channel.id, is_active: e.target.checked })
                        }
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {channels?.length === 0 && (
        <div className="text-center py-12">
          <Bell className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No notification channels</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating a new notification channel.</p>
        </div>
      )}
    </div>
  )
}
