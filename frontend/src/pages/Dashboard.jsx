import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Wallet,
  Plus,
  Users,
  User,
  LogOut,
  ChevronRight,
  Globe,
  MapPin,
  Sparkles,
  Shield,
  Map,
  Trash2,
  Link2,
} from "lucide-react";
import { PlanViewer } from "@/components/PlanViewer";

const TRIP_COVERS = [
  "https://images.unsplash.com/photo-1628584547352-70ec34799bc1?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
  "https://images.unsplash.com/photo-1655431571078-3a6b9d385d63?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
  "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
  "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
];

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savedPlans, setSavedPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [newTrip, setNewTrip] = useState({
    name: "",
    description: "",
    currency: "INR",
    cover_image: TRIP_COVERS[0],
  });

  useEffect(() => {
    fetchTrips();
    fetchCurrencies();
    checkAdminStatus();
    fetchSavedPlans();
  }, []);

  const checkAdminStatus = async () => {
    try {
      const response = await axios.get(`${API}/admin/check`, {
        withCredentials: true,
      });
      setIsAdmin(response.data.is_admin);
    } catch (error) {
      setIsAdmin(false);
    }
  };

  const fetchTrips = async () => {
    try {
      const response = await axios.get(`${API}/trips`, {
        withCredentials: true,
      });
      setTrips(response.data);
    } catch (error) {
      console.error("Error fetching trips:", error);
      toast.error("Failed to load trips");
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrencies = async () => {
    try {
      const response = await axios.get(`${API}/currencies`);
      setCurrencies(response.data);
    } catch (error) {
      console.error("Error fetching currencies:", error);
    }
  };

  const fetchSavedPlans = async () => {
    try {
      const response = await axios.get(`${API}/user/plans`, {
        withCredentials: true,
      });
      setSavedPlans(response.data || []);
    } catch (error) {
      console.error("Error fetching saved plans:", error);
    }
  };

  const handleCreateTrip = async (e) => {
    e.preventDefault();
    if (!newTrip.name.trim()) {
      toast.error("Please enter a trip name");
      return;
    }

    try {
      const response = await axios.post(`${API}/trips`, newTrip, {
        withCredentials: true,
      });
      setTrips([response.data, ...trips]);
      setCreateDialogOpen(false);
      setNewTrip({
        name: "",
        description: "",
        currency: "INR",
        cover_image: TRIP_COVERS[Math.floor(Math.random() * TRIP_COVERS.length)],
      });
      toast.success("Trip created successfully!");
    } catch (error) {
      console.error("Error creating trip:", error);
      toast.error("Failed to create trip");
    }
  };

  const getCurrencySymbol = (code) => {
    const currency = currencies.find((c) => c.code === code);
    return currency?.symbol || code;
  };

  const totalBalance = trips.reduce((sum, trip) => sum + trip.your_balance, 0);

  return (
    <div className="min-h-screen bg-background relative z-10">
      {/* Header */}
      <header className="sticky top-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wallet className="w-8 h-8 text-primary" />
            <span className="font-heading text-xl font-bold tracking-tight">
              EZ Trip
            </span>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="flex items-center gap-3 px-3"
                data-testid="user-menu-btn"
              >
                <Avatar className="w-8 h-8">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback>
                    {user?.name?.charAt(0) || "U"}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden sm:inline text-sm font-medium">
                  {user?.name}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="px-3 py-2">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => navigate("/profile")}
                data-testid="profile-menu-btn"
              >
                <User className="w-4 h-4 mr-2" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => setCreateDialogOpen(true)}
                data-testid="create-trip-menu-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create New Trip
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => navigate("/planner")}
                data-testid="planner-menu-btn"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                AI Trip Planner
              </DropdownMenuItem>
              {isAdmin && (
                <DropdownMenuItem
                  onClick={() => navigate("/admin")}
                  data-testid="admin-menu-btn"
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Admin Panel
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={logout}
                className="text-destructive focus:text-destructive"
                data-testid="logout-btn"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Welcome Section */}
        <div className="mb-12 animate-fade-in">
          <h1 className="font-heading text-4xl sm:text-5xl font-bold mb-2">
            Welcome back, {user?.name?.split(" ")[0]}
          </h1>
          <p className="text-muted-foreground text-lg">
            Manage your trips and track shared expenses
          </p>
        </div>

        {/* Balance Overview */}
        <div className="grid grid-cols-1 xs:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-12 stagger-children">
          <div className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0">
            <p className="text-sm text-muted-foreground mb-1">Overall Balance</p>
            <p
              className={`font-heading text-3xl font-bold ${totalBalance >= 0 ? "balance-positive" : "balance-negative"
                }`}
              data-testid="overall-balance"
            >
              {totalBalance >= 0 ? "+" : ""}
              {totalBalance.toFixed(2)}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {totalBalance >= 0
                ? "You are owed money"
                : "You owe money"}
            </p>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0">
            <p className="text-sm text-muted-foreground mb-1">Active Trips</p>
            <p className="font-heading text-3xl font-bold" data-testid="active-trips-count">
              {trips.length}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {trips.length === 1 ? "trip" : "trips"} in progress
            </p>
          </div>

          {/* AI Trip Planner Card */}
          <div
            onClick={() => navigate("/planner")}
            className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-xl p-6 animate-fade-in opacity-0 cursor-pointer card-hover"
            data-testid="ai-planner-card"
          >
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <p className="text-sm font-medium text-primary">AI Powered</p>
            </div>
            <p className="font-heading text-xl font-bold mb-1">Trip Planner</p>
            <p className="text-sm text-muted-foreground">
              Get weather, costs & itinerary
            </p>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0">
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  className="w-full h-full min-h-[80px] rounded-xl font-bold tracking-wide btn-glow flex flex-col items-center justify-center gap-2"
                  data-testid="create-trip-btn"
                >
                  <Plus className="w-8 h-8" />
                  <span>Create New Trip</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle className="font-heading text-2xl">
                    Create New Trip
                  </DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreateTrip} className="space-y-6 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="trip-name">Trip Name</Label>
                    <Input
                      id="trip-name"
                      placeholder="Beach Vacation 2025"
                      value={newTrip.name}
                      onChange={(e) =>
                        setNewTrip({ ...newTrip, name: e.target.value })
                      }
                      className="h-12"
                      data-testid="trip-name-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="trip-description">Description (optional)</Label>
                    <Input
                      id="trip-description"
                      placeholder="Annual trip with friends"
                      value={newTrip.description}
                      onChange={(e) =>
                        setNewTrip({ ...newTrip, description: e.target.value })
                      }
                      className="h-12"
                      data-testid="trip-description-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="trip-currency">Default Currency</Label>
                    <Select
                      value={newTrip.currency}
                      onValueChange={(value) =>
                        setNewTrip({ ...newTrip, currency: value })
                      }
                    >
                      <SelectTrigger className="h-12" data-testid="trip-currency-select">
                        <SelectValue placeholder="Select currency" />
                      </SelectTrigger>
                      <SelectContent>
                        {currencies.map((currency) => (
                          <SelectItem key={currency.code} value={currency.code}>
                            {currency.symbol} {currency.name} ({currency.code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Cover Image</Label>
                    <div className="grid grid-cols-4 gap-2">
                      {TRIP_COVERS.map((cover, index) => (
                        <button
                          key={index}
                          type="button"
                          onClick={() =>
                            setNewTrip({ ...newTrip, cover_image: cover })
                          }
                          className={`aspect-square rounded-lg overflow-hidden border-2 transition-colors ${newTrip.cover_image === cover
                            ? "border-primary"
                            : "border-transparent hover:border-border"
                            }`}
                        >
                          <img
                            src={cover}
                            alt={`Cover ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                        </button>
                      ))}
                    </div>
                  </div>

                  <Button
                    type="submit"
                    className="w-full h-12 rounded-full font-bold tracking-wide btn-glow"
                    data-testid="submit-create-trip-btn"
                  >
                    Create Trip
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Trips List */}
        <div className="space-y-6">
          <h2 className="font-heading text-2xl font-bold">Your Trips</h2>

          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="bg-card border border-border rounded-xl h-64 animate-pulse"
                />
              ))}
            </div>
          ) : trips.length === 0 ? (
            <div className="bg-card border border-border rounded-xl p-12 text-center">
              <MapPin className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="font-heading text-xl font-bold mb-2">
                No trips yet
              </h3>
              <p className="text-muted-foreground mb-6">
                Create your first trip to start tracking expenses
              </p>
              <Button
                onClick={() => setCreateDialogOpen(true)}
                className="rounded-full font-bold tracking-wide btn-glow"
                data-testid="empty-create-trip-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Trip
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 stagger-children">
              {trips.map((trip, index) => (
                <div
                  key={trip.trip_id}
                  onClick={() => navigate(`/trip/${trip.trip_id}`)}
                  className="bg-card border border-border rounded-xl overflow-hidden card-hover cursor-pointer animate-fade-in opacity-0"
                  data-testid={`trip-card-${trip.trip_id}`}
                >
                  {/* Cover Image */}
                  <div className="h-32 bg-secondary relative overflow-hidden">
                    {trip.cover_image && (
                      <img
                        src={trip.cover_image}
                        alt={trip.name}
                        className="w-full h-full object-cover"
                      />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-card to-transparent" />
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-heading text-xl font-bold mb-1">
                          {trip.name}
                        </h3>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Users className="w-4 h-4" />
                          <span>{trip.members.length} members</span>
                          <Globe className="w-4 h-4 ml-2" />
                          <span>{trip.currency}</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-muted-foreground" />
                    </div>

                    <div className="flex items-end justify-between pt-4 border-t border-border">
                      <div>
                        <p className="text-sm text-muted-foreground">
                          Total expenses
                        </p>
                        <p className="font-heading text-lg font-bold">
                          {getCurrencySymbol(trip.currency)}
                          {trip.total_expenses.toFixed(2)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">
                          Your balance
                        </p>
                        <p
                          className={`font-heading text-lg font-bold ${trip.your_balance >= 0
                            ? "balance-positive"
                            : "balance-negative"
                            }`}
                        >
                          {trip.your_balance >= 0 ? "+" : ""}
                          {getCurrencySymbol(trip.currency)}
                          {Math.abs(trip.your_balance).toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Native Ad Slot */}
              {trips.length > 0 && (
                <div className="bg-card border border-border rounded-xl overflow-hidden card-hover animate-fade-in opacity-0 relative">
                  <span className="absolute top-4 right-4 z-10 bg-white/10 text-xs px-2 py-1 rounded uppercase tracking-widest text-muted-foreground">
                    Sponsored
                  </span>
                  <div className="h-32 bg-secondary relative overflow-hidden">
                    <div className="w-full h-full bg-gradient-to-br from-primary/20 to-secondary flex items-center justify-center">
                      <Globe className="w-16 h-16 text-primary/50" />
                    </div>
                  </div>
                  <div className="p-6">
                    <h3 className="font-heading text-xl font-bold mb-1">
                      Currency Exchange
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Get the best rates for your international trips
                    </p>
                    <Button
                      variant="outline"
                      className="w-full rounded-full"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Learn More
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* My Saved Plans Section */}
        <div className="space-y-6 mt-12 animate-slide-up">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-heading text-2xl font-bold">My Trip Plans</h2>
              <p className="text-muted-foreground">AI-generated plans you've saved</p>
            </div>
            <Button onClick={() => navigate("/planner")} variant="outline">
              <Sparkles className="w-4 h-4 mr-2" />
              Create New Plan
            </Button>
          </div>

          {savedPlans.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {savedPlans.map((plan) => (
                <div
                  key={plan.plan_id}
                  className="bg-card border border-border rounded-xl p-6 card-hover animate-fade-in opacity-0 cursor-pointer"
                  onClick={() => setSelectedPlan(plan)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <Map className="w-5 h-5 text-primary mt-1" />
                      <div>
                        <h3 className="font-heading font-bold">{plan.destination}</h3>
                        <p className="text-sm text-muted-foreground">
                          {plan.start_date} - {plan.end_date}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive h-8 w-8"
                      onClick={async (e) => {
                        e.stopPropagation();
                        try {
                          await axios.delete(`${API}/user/plans/${plan.plan_id}`, {
                            withCredentials: true,
                          });
                          setSavedPlans(savedPlans.filter(p => p.plan_id !== plan.plan_id));
                          toast.success("Plan deleted");
                        } catch (error) {
                          toast.error("Failed to delete plan");
                        }
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>

                  {plan.itinerary && plan.itinerary.length > 0 && (
                    <div className="mb-4 text-sm text-muted-foreground">
                      {plan.itinerary.length} days planned
                    </div>
                  )}

                  {plan.linked_to_trip ? (
                    <div className="flex items-center gap-2 text-sm text-primary">
                      <Link2 className="w-4 h-4" />
                      Linked to a trip
                    </div>
                  ) : (
                    <Select
                      value=""
                      onOpenChange={(open) => {
                        if (!open) return;
                      }}
                      onValueChange={async (tripId) => {
                        if (!tripId) return;

                        try {
                          await axios.post(
                            `${API}/trips/${tripId}/link-plan`,
                            { plan_id: plan.plan_id },
                            { withCredentials: true }
                          );
                          toast.success("Plan linked to trip!");
                          fetchSavedPlans();
                        } catch (error) {
                          toast.error("Failed to link plan");
                        }
                      }}
                    >
                      <SelectTrigger className="h-12">
                        <SelectValue placeholder="Link to a trip..." />
                      </SelectTrigger>
                      <SelectContent>
                        {trips.map((trip) => (
                          <SelectItem key={trip.trip_id} value={trip.trip_id}>
                            {trip.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-card border border-border rounded-xl p-12 text-center">
              <Map className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
              <h3 className="font-heading text-xl font-bold mb-2">No Plans Saved Yet</h3>
              <p className="text-muted-foreground mb-6">
                Generate trip plans with AI and save them here for easy access
              </p>
              <Button onClick={() => navigate("/planner")} className="btn-glow">
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Your First Plan
              </Button>
            </div>
          )}
        </div>

        {/* Plan Viewer Dialog */}
        <Dialog open={!!selectedPlan} onOpenChange={() => setSelectedPlan(null)}>
          <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto top-[5%] translate-y-0">
            {selectedPlan && (
              <PlanViewer plan={selectedPlan} />
            )}
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
};

export default Dashboard;
