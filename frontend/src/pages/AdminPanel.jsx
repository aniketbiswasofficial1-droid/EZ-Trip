import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Shield,
  Users,
  MapPin,
  Settings,
  BarChart3,
  FileText,
  ToggleLeft,
  Sparkles,
  ArrowLeft,
  Trash2,
  UserCog,
  Ban,
  Check,
  RefreshCw,
  Save,
  Loader2,
  DollarSign,
  Globe,
  TrendingUp,
} from "lucide-react";

const AdminPanel = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Data states
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [trips, setTrips] = useState([]);
  const [features, setFeatures] = useState([]);
  const [content, setContent] = useState([]);
  const [settings, setSettings] = useState(null);
  
  // Pagination
  const [userPage, setUserPage] = useState(0);
  const [tripPage, setTripPage] = useState(0);
  const [totalUsers, setTotalUsers] = useState(0);
  const [totalTrips, setTotalTrips] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    checkAdminAccess();
  }, []);

  const checkAdminAccess = async () => {
    try {
      const response = await axios.get(`${API}/admin/check`, {
        withCredentials: true,
      });
      
      if (response.data.is_admin) {
        setIsAdmin(true);
        await loadAllData();
      } else {
        toast.error("Admin access required");
        navigate("/dashboard");
      }
    } catch (error) {
      console.error("Admin check error:", error);
      toast.error("Admin access required");
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const loadAllData = async () => {
    await Promise.all([
      fetchStats(),
      fetchUsers(),
      fetchTrips(),
      fetchFeatures(),
      fetchContent(),
      fetchSettings(),
    ]);
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`, {
        withCredentials: true,
      });
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchUsers = async (page = 0) => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        params: { skip: page * pageSize, limit: pageSize },
        withCredentials: true,
      });
      setUsers(response.data.users);
      setTotalUsers(response.data.total);
      setUserPage(page);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  const fetchTrips = async (page = 0) => {
    try {
      const response = await axios.get(`${API}/admin/trips`, {
        params: { skip: page * pageSize, limit: pageSize },
        withCredentials: true,
      });
      setTrips(response.data.trips);
      setTotalTrips(response.data.total);
      setTripPage(page);
    } catch (error) {
      console.error("Error fetching trips:", error);
    }
  };

  const fetchFeatures = async () => {
    try {
      const response = await axios.get(`${API}/admin/features`, {
        withCredentials: true,
      });
      setFeatures(response.data);
    } catch (error) {
      console.error("Error fetching features:", error);
    }
  };

  const fetchContent = async () => {
    try {
      const response = await axios.get(`${API}/admin/content`, {
        withCredentials: true,
      });
      setContent(response.data);
    } catch (error) {
      console.error("Error fetching content:", error);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`, {
        withCredentials: true,
      });
      setSettings(response.data);
    } catch (error) {
      console.error("Error fetching settings:", error);
    }
  };

  // User actions
  const toggleUserAdmin = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/toggle-admin`, {}, {
        withCredentials: true,
      });
      toast.success("Admin status updated");
      fetchUsers(userPage);
    } catch (error) {
      toast.error("Failed to update admin status");
    }
  };

  const toggleUserStatus = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/toggle-status`, {}, {
        withCredentials: true,
      });
      toast.success("User status updated");
      fetchUsers(userPage);
    } catch (error) {
      toast.error("Failed to update user status");
    }
  };

  // Trip actions
  const deleteTrip = async (tripId) => {
    try {
      await axios.delete(`${API}/admin/trips/${tripId}`, {
        withCredentials: true,
      });
      toast.success("Trip deleted");
      fetchTrips(tripPage);
      fetchStats();
    } catch (error) {
      toast.error("Failed to delete trip");
    }
  };

  // Feature toggle
  const updateFeature = async (featureId, enabled) => {
    try {
      await axios.put(`${API}/admin/features/${featureId}`, null, {
        params: { enabled },
        withCredentials: true,
      });
      setFeatures(features.map(f => 
        f.feature_id === featureId ? { ...f, enabled } : f
      ));
      toast.success("Feature updated");
    } catch (error) {
      toast.error("Failed to update feature");
    }
  };

  // Content update
  const updateContent = async (contentId, value) => {
    try {
      await axios.put(`${API}/admin/content/${contentId}`, null, {
        params: { value },
        withCredentials: true,
      });
      setContent(content.map(c => 
        c.content_id === contentId ? { ...c, value } : c
      ));
      toast.success("Content updated");
    } catch (error) {
      toast.error("Failed to update content");
    }
  };

  // Settings update
  const saveSettings = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/settings`, settings, {
        withCredentials: true,
      });
      toast.success("Settings saved");
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const groupFeaturesByCategory = () => {
    const grouped = {};
    features.forEach(f => {
      if (!grouped[f.category]) grouped[f.category] = [];
      grouped[f.category].push(f);
    });
    return grouped;
  };

  const groupContentBySection = () => {
    const grouped = {};
    content.forEach(c => {
      if (!grouped[c.section]) grouped[c.section] = [];
      grouped[c.section].push(c);
    });
    return grouped;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/dashboard")}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-primary" />
              <span className="font-heading text-lg font-bold">Admin Panel</span>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAllData}
            className="rounded-full"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="bg-secondary/50 p-1 rounded-full flex-wrap h-auto gap-1">
            <TabsTrigger value="dashboard" className="rounded-full">
              <BarChart3 className="w-4 h-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="users" className="rounded-full">
              <Users className="w-4 h-4 mr-2" />
              Users
            </TabsTrigger>
            <TabsTrigger value="trips" className="rounded-full">
              <MapPin className="w-4 h-4 mr-2" />
              Trips
            </TabsTrigger>
            <TabsTrigger value="features" className="rounded-full">
              <ToggleLeft className="w-4 h-4 mr-2" />
              Features
            </TabsTrigger>
            <TabsTrigger value="content" className="rounded-full">
              <FileText className="w-4 h-4 mr-2" />
              Content
            </TabsTrigger>
            <TabsTrigger value="settings" className="rounded-full">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {stats && (
              <>
                {/* Stats Grid */}
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-card border border-border rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <Users className="w-5 h-5 text-primary" />
                      <span className="text-sm text-muted-foreground">Total Users</span>
                    </div>
                    <p className="font-heading text-3xl font-bold">{stats.total_users}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      +{stats.new_users_this_week} this week
                    </p>
                  </div>

                  <div className="bg-card border border-border rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <MapPin className="w-5 h-5 text-primary" />
                      <span className="text-sm text-muted-foreground">Total Trips</span>
                    </div>
                    <p className="font-heading text-3xl font-bold">{stats.total_trips}</p>
                  </div>

                  <div className="bg-card border border-border rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <DollarSign className="w-5 h-5 text-primary" />
                      <span className="text-sm text-muted-foreground">Total Expenses</span>
                    </div>
                    <p className="font-heading text-3xl font-bold">{stats.total_expenses}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {stats.total_refunds} refunds
                    </p>
                  </div>

                  <div className="bg-card border border-border rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <Sparkles className="w-5 h-5 text-primary" />
                      <span className="text-sm text-muted-foreground">AI Plans</span>
                    </div>
                    <p className="font-heading text-3xl font-bold">{stats.total_saved_plans}</p>
                  </div>
                </div>

                {/* Charts Row */}
                <div className="grid lg:grid-cols-2 gap-6">
                  {/* Popular Destinations */}
                  <div className="bg-card border border-border rounded-xl p-6">
                    <h3 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-primary" />
                      Popular Destinations
                    </h3>
                    {stats.popular_destinations.length > 0 ? (
                      <div className="space-y-3">
                        {stats.popular_destinations.map((dest, idx) => (
                          <div key={idx} className="flex items-center justify-between">
                            <span>{dest.destination}</span>
                            <span className="text-primary font-bold">{dest.count} plans</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No data yet</p>
                    )}
                  </div>

                  {/* Expenses by Currency */}
                  <div className="bg-card border border-border rounded-xl p-6">
                    <h3 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                      <Globe className="w-5 h-5 text-primary" />
                      Expenses by Currency
                    </h3>
                    {stats.expense_by_currency.length > 0 ? (
                      <div className="space-y-3">
                        {stats.expense_by_currency.map((curr, idx) => (
                          <div key={idx} className="flex items-center justify-between">
                            <span>{curr.currency}</span>
                            <div className="text-right">
                              <span className="text-primary font-bold">{curr.total.toFixed(2)}</span>
                              <span className="text-muted-foreground text-sm ml-2">({curr.count} expenses)</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No data yet</p>
                    )}
                  </div>
                </div>
              </>
            )}
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-4">
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <div className="p-4 border-b border-border">
                <h3 className="font-heading text-lg font-bold">User Management</h3>
                <p className="text-sm text-muted-foreground">
                  {totalUsers} total users
                </p>
              </div>
              <ScrollArea className="h-[500px]">
                <div className="divide-y divide-border">
                  {users.map((u) => (
                    <div key={u.user_id} className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Avatar className="w-10 h-10">
                          <AvatarImage src={u.picture} />
                          <AvatarFallback>{u.name?.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{u.name}</p>
                            {u.is_admin && (
                              <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                                Admin
                              </span>
                            )}
                            {u.disabled && (
                              <span className="text-xs bg-destructive/20 text-destructive px-2 py-0.5 rounded-full">
                                Disabled
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{u.email}</p>
                          <p className="text-xs text-muted-foreground">{u.trip_count} trips</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleUserAdmin(u.user_id)}
                          disabled={u.user_id === user?.user_id}
                        >
                          <UserCog className="w-4 h-4 mr-1" />
                          {u.is_admin ? "Remove Admin" : "Make Admin"}
                        </Button>
                        <Button
                          variant={u.disabled ? "default" : "destructive"}
                          size="sm"
                          onClick={() => toggleUserStatus(u.user_id)}
                          disabled={u.user_id === user?.user_id}
                        >
                          {u.disabled ? <Check className="w-4 h-4 mr-1" /> : <Ban className="w-4 h-4 mr-1" />}
                          {u.disabled ? "Enable" : "Disable"}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
              {/* Pagination */}
              <div className="p-4 border-t border-border flex justify-between items-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchUsers(userPage - 1)}
                  disabled={userPage === 0}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {userPage + 1} of {Math.ceil(totalUsers / pageSize)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchUsers(userPage + 1)}
                  disabled={(userPage + 1) * pageSize >= totalUsers}
                >
                  Next
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* Trips Tab */}
          <TabsContent value="trips" className="space-y-4">
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <div className="p-4 border-b border-border">
                <h3 className="font-heading text-lg font-bold">Trip Management</h3>
                <p className="text-sm text-muted-foreground">
                  {totalTrips} total trips
                </p>
              </div>
              <ScrollArea className="h-[500px]">
                <div className="divide-y divide-border">
                  {trips.map((trip) => (
                    <div key={trip.trip_id} className="p-4 flex items-center justify-between">
                      <div>
                        <p className="font-medium">{trip.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {trip.members?.length || 0} members • {trip.expense_count} expenses • {trip.currency}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Created by: {trip.created_by}
                        </p>
                      </div>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="destructive" size="sm">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Trip?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This will permanently delete "{trip.name}" and all its expenses.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => deleteTrip(trip.trip_id)}
                              className="bg-destructive"
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  ))}
                </div>
              </ScrollArea>
              {/* Pagination */}
              <div className="p-4 border-t border-border flex justify-between items-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchTrips(tripPage - 1)}
                  disabled={tripPage === 0}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {tripPage + 1} of {Math.ceil(totalTrips / pageSize)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchTrips(tripPage + 1)}
                  disabled={(tripPage + 1) * pageSize >= totalTrips}
                >
                  Next
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* Features Tab */}
          <TabsContent value="features" className="space-y-6">
            {Object.entries(groupFeaturesByCategory()).map(([category, categoryFeatures]) => (
              <div key={category} className="bg-card border border-border rounded-xl p-6">
                <h3 className="font-heading text-lg font-bold mb-4 capitalize">
                  {category} Features
                </h3>
                <div className="space-y-4">
                  {categoryFeatures.map((feature) => (
                    <div
                      key={feature.feature_id}
                      className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{feature.name}</p>
                        <p className="text-sm text-muted-foreground">{feature.description}</p>
                      </div>
                      <Switch
                        checked={feature.enabled}
                        onCheckedChange={(checked) => updateFeature(feature.feature_id, checked)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </TabsContent>

          {/* Content Tab */}
          <TabsContent value="content" className="space-y-6">
            {Object.entries(groupContentBySection()).map(([section, sectionContent]) => (
              <div key={section} className="bg-card border border-border rounded-xl p-6">
                <h3 className="font-heading text-lg font-bold mb-4 capitalize">
                  {section} Section
                </h3>
                <div className="space-y-4">
                  {sectionContent.map((item) => (
                    <div key={item.content_id} className="space-y-2">
                      <Label className="capitalize">{item.key.replace(/_/g, " ")}</Label>
                      {item.value.length > 100 ? (
                        <Textarea
                          value={item.value}
                          onChange={(e) => {
                            setContent(content.map(c =>
                              c.content_id === item.content_id ? { ...c, value: e.target.value } : c
                            ));
                          }}
                          onBlur={() => updateContent(item.content_id, item.value)}
                          className="min-h-[100px]"
                        />
                      ) : (
                        <Input
                          value={item.value}
                          onChange={(e) => {
                            setContent(content.map(c =>
                              c.content_id === item.content_id ? { ...c, value: e.target.value } : c
                            ));
                          }}
                          onBlur={() => updateContent(item.content_id, item.value)}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            {settings && (
              <>
                {/* AI Settings */}
                <div className="bg-card border border-border rounded-xl p-6">
                  <h3 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary" />
                    AI Configuration
                  </h3>
                  <div className="space-y-4">
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>LLM Provider</Label>
                        <Select
                          value={settings.llm_provider}
                          onValueChange={(value) => setSettings({ ...settings, llm_provider: value, llm_model: settings.available_models[value]?.[0]?.id || "gpt-4o" })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="openai">OpenAI</SelectItem>
                            <SelectItem value="anthropic">Anthropic</SelectItem>
                            <SelectItem value="gemini">Google Gemini</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Model</Label>
                        <Select
                          value={settings.llm_model}
                          onValueChange={(value) => setSettings({ ...settings, llm_model: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {settings.available_models[settings.llm_provider]?.map((model) => (
                              <SelectItem key={model.id} value={model.id}>
                                {model.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>LLM API Key</Label>
                      <Input
                        type="password"
                        placeholder="Enter API key or leave empty for Emergent key"
                        value={settings.llm_key || ""}
                        onChange={(e) => setSettings({ ...settings, llm_key: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground">
                        Leave empty to use Emergent Universal Key
                      </p>
                    </div>
                  </div>
                </div>

                {/* App Settings */}
                <div className="bg-card border border-border rounded-xl p-6">
                  <h3 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                    <Settings className="w-5 h-5 text-primary" />
                    App Settings
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                      <div>
                        <p className="font-medium">Maintenance Mode</p>
                        <p className="text-sm text-muted-foreground">Disable app for users</p>
                      </div>
                      <Switch
                        checked={settings.maintenance_mode}
                        onCheckedChange={(checked) => setSettings({ ...settings, maintenance_mode: checked })}
                      />
                    </div>
                    <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                      <div>
                        <p className="font-medium">Registration Enabled</p>
                        <p className="text-sm text-muted-foreground">Allow new user signups</p>
                      </div>
                      <Switch
                        checked={settings.registration_enabled}
                        onCheckedChange={(checked) => setSettings({ ...settings, registration_enabled: checked })}
                      />
                    </div>
                    <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                      <div>
                        <p className="font-medium">AI Trip Planner</p>
                        <p className="text-sm text-muted-foreground">Enable AI planning feature</p>
                      </div>
                      <Switch
                        checked={settings.ai_planner_enabled}
                        onCheckedChange={(checked) => setSettings({ ...settings, ai_planner_enabled: checked })}
                      />
                    </div>

                    <div className="grid sm:grid-cols-2 gap-4 pt-4">
                      <div className="space-y-2">
                        <Label>Max Trips per User</Label>
                        <Input
                          type="number"
                          value={settings.max_trips_per_user}
                          onChange={(e) => setSettings({ ...settings, max_trips_per_user: parseInt(e.target.value) })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Max Members per Trip</Label>
                        <Input
                          type="number"
                          value={settings.max_members_per_trip}
                          onChange={(e) => setSettings({ ...settings, max_members_per_trip: parseInt(e.target.value) })}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Default Currency</Label>
                      <Select
                        value={settings.default_currency}
                        onValueChange={(value) => setSettings({ ...settings, default_currency: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="USD">USD - US Dollar</SelectItem>
                          <SelectItem value="EUR">EUR - Euro</SelectItem>
                          <SelectItem value="GBP">GBP - British Pound</SelectItem>
                          <SelectItem value="INR">INR - Indian Rupee</SelectItem>
                          <SelectItem value="JPY">JPY - Japanese Yen</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>

                {/* Save Button */}
                <Button
                  onClick={saveSettings}
                  disabled={saving}
                  className="w-full rounded-full font-bold btn-glow"
                >
                  {saving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  Save Settings
                </Button>
              </>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default AdminPanel;
