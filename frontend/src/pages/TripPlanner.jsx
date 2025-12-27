import { useState } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { LocationAutocomplete } from "@/components/LocationAutocomplete";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Wallet,
  ArrowLeft,
  Sparkles,
  MapPin,
  Calendar as CalendarIcon,
  Users,
  User,
  Plane,
  Train,
  Bus,
  Hotel,
  Utensils,
  Activity,
  Car,
  CloudSun,
  DollarSign,
  Lightbulb,
  Package,
  Heart,
  Phone,
  LogOut,
  Save,
  Loader2,
  Plus,
} from "lucide-react";
import { format, addDays } from "date-fns";

const INTERESTS = [
  { id: "adventure", label: "Adventure", icon: Activity },
  { id: "culture", label: "Culture & History", icon: Hotel },
  { id: "food", label: "Food & Dining", icon: Utensils },
  { id: "relaxation", label: "Relaxation", icon: CloudSun },
  { id: "nature", label: "Nature", icon: MapPin },
  { id: "shopping", label: "Shopping", icon: Package },
  { id: "nightlife", label: "Nightlife", icon: Sparkles },
  { id: "photography", label: "Photography", icon: Heart },
];

const TripPlanner = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});

  // Form state
  const [destination, setDestination] = useState(null);
  const [departureLocation, setDepartureLocation] = useState(null);
  const [startDate, setStartDate] = useState(addDays(new Date(), 7));
  const [endDate, setEndDate] = useState(addDays(new Date(), 14));
  const [numTravelers, setNumTravelers] = useState(2);
  const [budgetPreference, setBudgetPreference] = useState("moderate");
  const [currency, setCurrency] = useState("INR"); // Default to INR for India focus
  const [interests, setInterests] = useState([]);
  const [accommodationType, setAccommodationType] = useState("hotel");
  const [departureTransport, setDepartureTransport] = useState("flight");
  const [returnTransport, setReturnTransport] = useState("flight");

  const handleInterestToggle = (interestId) => {
    setInterests((prev) =>
      prev.includes(interestId)
        ? prev.filter((i) => i !== interestId)
        : [...prev, interestId]
    );
  };

  const handleGeneratePlan = async () => {
    const newErrors = {};

    if (!destination) {
      newErrors.destination = "Please select a destination";
    }

    if (!startDate || !endDate) {
      newErrors.dates = "Please select travel dates";
    }

    if (startDate && endDate && startDate > endDate) {
      newErrors.dates = "End date must be after start date";
    }

    if ((departureTransport !== "none" || returnTransport !== "none") && !departureLocation) {
      newErrors.departureLocation = "Please select your departure location";
    }

    if (!numTravelers || numTravelers < 1) {
      newErrors.numTravelers = "Please enter at least 1 traveler";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      toast.error(Object.values(newErrors)[0]);
      return;
    }

    setErrors({});
    setLoading(true);
    setPlan(null);

    try {
      const response = await axios.post(
        `${API}/planner/generate`,
        {
          destination: destination.name,
          start_date: format(startDate, "yyyy-MM-dd"),
          end_date: format(endDate, "yyyy-MM-dd"),
          num_travelers: Number(numTravelers) || 1,
          budget_preference: budgetPreference,
          currency: currency,
          interests,
          accommodation_type: accommodationType,
          departure_transport: departureTransport,
          return_transport: returnTransport,
          departure_city: (departureTransport !== "none" || returnTransport !== "none") ? departureLocation?.name : null,
        },
        { withCredentials: true }
      );

      setPlan(response.data);
      toast.success("Trip plan generated!");
    } catch (error) {
      console.error("Error generating plan:", error);
      toast.error(error.response?.data?.detail || "Failed to generate plan. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePlan = async () => {
    if (!plan) return;

    setSaving(true);
    try {
      const planData = {
        destination: plan.destination,
        start_date: plan.start_date,
        end_date: plan.end_date,
        num_days: plan.num_days,
        num_travelers: plan.num_travelers,
        itinerary: plan.itinerary || [],
        best_time_to_visit: plan.best_time_to_visit || "",
        weather_summary: plan.weather_summary || "",
        cost_breakdown: plan.cost_breakdown || null,
        departure_transport_details: plan.departure_transport_details || null,
        return_transport_details: plan.return_transport_details || null,
        travel_tips: plan.travel_tips || [],
        packing_suggestions: plan.packing_suggestions || [],
        packing_suggestions_detailed: plan.packing_suggestions_detailed || [],
        local_customs: plan.local_customs || [],
        emergency_contacts: plan.emergency_contacts || {},
      };

      await axios.post(`${API}/user/plans`, planData, { withCredentials: true });
      toast.success("Trip plan saved to your profile!");
    } catch (error) {
      console.error("Error saving plan:", error);
      toast.error("Failed to save plan");
    } finally {
      setSaving(false);
    }
  };

  const getCurrencySymbol = (curr) => {
    const symbols = { USD: "$", EUR: "€", GBP: "£", INR: "₹", JPY: "¥", AUD: "A$", SGD: "S$", THB: "฿" };
    return symbols[curr] || curr;
  };

  return (
    <div className="min-h-screen bg-background relative z-10">
      {/* Header */}
      <header className="sticky top-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/dashboard")}
              data-testid="back-btn"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-primary" />
              <span className="font-heading text-lg font-bold tracking-tight">
                AI Trip Planner
              </span>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-3 px-3">
                <Avatar className="w-8 h-8">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback>{user?.name?.charAt(0) || "U"}</AvatarFallback>
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
              <DropdownMenuItem onClick={() => navigate("/profile")}>
                <User className="w-4 h-4 mr-2" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                <Plus className="w-4 h-4 mr-2" />
                Create New Trip
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                <Wallet className="w-4 h-4 mr-2" />
                Dashboard
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-destructive">
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          {/* Left: Form */}
          <div className="space-y-6">
            <div className="animate-fade-in">
              <h1 className="font-heading text-4xl font-bold mb-2">
                Plan Your Perfect Trip
              </h1>
              <p className="text-muted-foreground">
                Let AI create a personalized itinerary with weather, costs, and recommendations
              </p>
            </div>

            <div className="bg-card border border-border rounded-xl p-4 sm:p-6 space-y-6 animate-slide-up">
              {/* Destination and Departure - With Autocomplete */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="departure-location">Departure</Label>
                  <LocationAutocomplete
                    value={departureLocation?.display_name || ""}
                    onChange={(location) => {
                      setDepartureLocation(location);
                      if (errors.departureLocation) setErrors({ ...errors, departureLocation: null });
                    }}
                    placeholder="Select departure location"
                    icon={Plane}
                    error={!!errors.departureLocation}
                  />
                  {errors.departureLocation && (
                    <p className="text-sm text-destructive">{errors.departureLocation}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="destination">Destination</Label>
                  <LocationAutocomplete
                    value={destination?.display_name || ""}
                    onChange={(location) => {
                      setDestination(location);
                      if (errors.destination) setErrors({ ...errors, destination: null });
                    }}
                    placeholder="Select destination"
                    icon={MapPin}
                    error={!!errors.destination}
                  />
                  {errors.destination && (
                    <p className="text-sm text-destructive">{errors.destination}</p>
                  )}
                </div>
              </div>

              {/* Transportation Selection */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-xs text-muted-foreground">Departure Transport</Label>
                    <Select value={departureTransport} onValueChange={setDepartureTransport}>
                      <SelectTrigger className="h-12" data-testid="departure-transport-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="flight">✈️ Flight</SelectItem>
                        <SelectItem value="train">🚆 Train</SelectItem>
                        <SelectItem value="bus">🚌 Bus</SelectItem>
                        <SelectItem value="none">No Transport</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs text-muted-foreground">Return Transport</Label>
                    <Select value={returnTransport} onValueChange={setReturnTransport}>
                      <SelectTrigger className="h-12" data-testid="return-transport-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="flight">✈️ Flight</SelectItem>
                        <SelectItem value="train">🚆 Train</SelectItem>
                        <SelectItem value="bus">🚌 Bus</SelectItem>
                        <SelectItem value="none">No Transport</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Date Range */}
              <div className="space-y-2">
                <Label>Travel Dates</Label>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">Start Date</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className="w-full justify-start text-left h-12"
                          data-testid="start-date-btn"
                        >
                          <CalendarIcon className="mr-2 h-4 w-4 text-muted-foreground" />
                          {startDate ? format(startDate, "MMM d, yyyy") : "Select"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={startDate}
                          onSelect={(date) => {
                            setStartDate(date);
                            if (date && endDate && date > endDate) {
                              setEndDate(addDays(date, 1));
                            }
                          }}
                          disabled={(date) => date < new Date()}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">End Date</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className="w-full justify-start text-left h-12"
                          data-testid="end-date-btn"
                        >
                          <CalendarIcon className="mr-2 h-4 w-4 text-muted-foreground" />
                          {endDate ? format(endDate, "MMM d, yyyy") : "Select"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={endDate}
                          onSelect={setEndDate}
                          disabled={(date) => date < (startDate || new Date())}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
                {errors.dates && (
                  <p className="text-sm text-destructive">{errors.dates}</p>
                )}
              </div>

              {/* Preferences Grid - Row 1: Travelers & Currency */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                {/* Travelers */}
                <div className="space-y-2">
                  <Label>Number of Travelers</Label>
                  <div className="flex items-center gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="h-12 w-12 shrink-0 rounded-full"
                      onClick={() => setNumTravelers(Math.max(1, (numTravelers || 1) - 1))}
                      disabled={numTravelers <= 1}
                    >
                      <span className="text-lg">−</span>
                    </Button>
                    <div className="relative flex-1">
                      <Input
                        type="number"
                        min={1}
                        max={50}
                        value={numTravelers}
                        onChange={(e) => {
                          const val = e.target.value;
                          setNumTravelers(val === "" ? "" : parseInt(val));
                        }}
                        className="h-12 text-center text-lg [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        placeholder="1"
                        data-testid="travelers-input"
                      />
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="h-12 w-12 shrink-0 rounded-full"
                      onClick={() => setNumTravelers(Math.min(50, (numTravelers || 1) + 1))}
                      disabled={numTravelers >= 50}
                    >
                      <span className="text-lg">+</span>
                    </Button>
                  </div>
                </div>

                {/* Currency */}
                <div className="space-y-2">
                  <Label>Currency</Label>
                  <Select value={currency} onValueChange={setCurrency}>
                    <SelectTrigger className="h-12" data-testid="currency-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="INR">₹ INR</SelectItem>
                      <SelectItem value="USD">$ USD</SelectItem>
                      <SelectItem value="EUR">€ EUR</SelectItem>
                      <SelectItem value="GBP">£ GBP</SelectItem>
                      <SelectItem value="AUD">A$ AUD</SelectItem>
                      <SelectItem value="SGD">S$ SGD</SelectItem>
                      <SelectItem value="THB">฿ THB</SelectItem>
                      <SelectItem value="JPY">¥ JPY</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Preferences Grid - Row 2: Budget & Accommodation */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                {/* Budget */}
                <div className="space-y-2">
                  <Label>Budget Preference</Label>
                  <Select value={budgetPreference} onValueChange={setBudgetPreference}>
                    <SelectTrigger className="h-12" data-testid="budget-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="budget">Budget-friendly</SelectItem>
                      <SelectItem value="moderate">Moderate</SelectItem>
                      <SelectItem value="luxury">Luxury</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Accommodation */}
                <div className="space-y-2">
                  <Label>Accommodation Type</Label>
                  <Select value={accommodationType} onValueChange={setAccommodationType}>
                    <SelectTrigger className="h-12" data-testid="accommodation-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hostel">Hostel</SelectItem>
                      <SelectItem value="hotel">Hotel</SelectItem>
                      <SelectItem value="airbnb">Airbnb</SelectItem>
                      <SelectItem value="resort">Resort</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Interests */}
              <div className="space-y-3">
                <Label>What interests you?</Label>
                <div className="grid grid-cols-2 gap-2">
                  {INTERESTS.map((interest) => {
                    const Icon = interest.icon;
                    const isSelected = interests.includes(interest.id);
                    return (
                      <button
                        key={interest.id}
                        type="button"
                        onClick={() => handleInterestToggle(interest.id)}
                        className={`flex items-center gap-2 p-3 rounded-lg border transition-all ${isSelected
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border hover:border-primary/50"
                          }`}
                        data-testid={`interest-${interest.id}`}
                      >
                        <Icon className="w-4 h-4" />
                        <span className="text-sm">{interest.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGeneratePlan}
                disabled={loading}
                className="w-full h-14 rounded-full font-bold tracking-wide btn-glow text-lg"
                data-testid="generate-plan-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Generating your perfect trip...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-2" />
                    Generate Trip Plan
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Right: Results */}
          <div className="space-y-6">
            {!plan && !loading && (
              <div className="bg-card border border-border rounded-xl p-12 text-center animate-fade-in">
                <Sparkles className="w-16 h-16 text-primary mx-auto mb-4 opacity-50" />
                <h3 className="font-heading text-xl font-bold mb-2">
                  Your trip plan will appear here
                </h3>
                <p className="text-muted-foreground">
                  Fill in your preferences and click generate to get a personalized itinerary
                </p>
              </div>
            )}

            {loading && (
              <div className="bg-card border border-border rounded-xl p-12 text-center animate-fade-in">
                <Loader2 className="w-16 h-16 text-primary mx-auto mb-4 animate-spin" />
                <h3 className="font-heading text-xl font-bold mb-2">
                  Planning your adventure...
                </h3>
                <p className="text-muted-foreground">
                  Analyzing weather, prices, and creating the perfect itinerary
                </p>
              </div>
            )}

            {plan && (
              <div className="space-y-6 animate-slide-up">
                {/* Header with Save */}
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-heading text-3xl font-bold mb-1">
                      {plan.destination}
                    </h2>
                    <p className="text-muted-foreground">
                      {plan.num_days} days • {plan.num_travelers} travelers
                    </p>
                  </div>
                  <Button
                    onClick={handleSavePlan}
                    disabled={saving}
                    variant="outline"
                    className="rounded-full"
                    data-testid="save-plan-btn"
                  >
                    {saving ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4 mr-2" />
                    )}
                    Save Plan
                  </Button>
                </div>

                {/* Cost Summary */}
                <div className="bg-card border border-border rounded-xl p-6">
                  <h3 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                    <span className="text-2xl">{getCurrencySymbol(plan.cost_breakdown.currency)}</span>
                    Cost Estimate (Per Person)
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
                    {[
                      { label: "Departure", value: plan.cost_breakdown.departure_transport, icon: Plane },
                      { label: "Return", value: plan.cost_breakdown.return_transport, icon: Plane },
                      { label: "Accommodation", value: plan.cost_breakdown.accommodation, icon: Hotel },
                      { label: "Food", value: plan.cost_breakdown.food, icon: Utensils },
                      { label: "Activities", value: plan.cost_breakdown.activities, icon: Activity },
                      { label: "Local Transport", value: plan.cost_breakdown.local_transportation, icon: Car },
                      { label: "Other", value: plan.cost_breakdown.miscellaneous, icon: Package },
                    ].map((item) => (
                      <div key={item.label} className="p-3 bg-secondary/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <item.icon className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">{item.label}</span>
                        </div>
                        <p className="font-heading font-bold">
                          {getCurrencySymbol(plan.cost_breakdown.currency)}
                          {item.value.toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between items-center pt-4 border-t border-border">
                    <div>
                      <p className="text-sm text-muted-foreground">Per Person</p>
                      <p className="font-heading text-2xl font-bold text-primary">
                        {getCurrencySymbol(plan.cost_breakdown.currency)}
                        {plan.cost_breakdown.total_per_person.toLocaleString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Total Group</p>
                      <p className="font-heading text-2xl font-bold">
                        {getCurrencySymbol(plan.cost_breakdown.currency)}
                        {plan.cost_breakdown.total_group.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Tabs for Details */}
                <Tabs defaultValue="itinerary" className="space-y-4">
                  <TabsList className="bg-secondary/50 p-1 rounded-full w-full grid grid-cols-6">
                    <TabsTrigger value="connectivity" className="rounded-full text-xs sm:text-sm">
                      Routes
                    </TabsTrigger>
                    <TabsTrigger value="itinerary" className="rounded-full text-xs sm:text-sm">
                      Day Plan
                    </TabsTrigger>
                    <TabsTrigger value="activities" className="rounded-full text-xs sm:text-sm">
                      Activities
                    </TabsTrigger>
                    <TabsTrigger value="tips" className="rounded-full text-xs sm:text-sm">
                      Tips
                    </TabsTrigger>
                    <TabsTrigger value="packing" className="rounded-full text-xs sm:text-sm">
                      Packing
                    </TabsTrigger>
                    <TabsTrigger value="info" className="rounded-full text-xs sm:text-sm">
                      Info
                    </TabsTrigger>
                  </TabsList>

                  {/* Connectivity Tab */}
                  <TabsContent value="connectivity">
                    <div className="space-y-4">
                      <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                          🚆✈️ Transport Connectivity & Journey Times
                        </h4>
                        <p className="text-sm text-muted-foreground mb-6">
                          Suggested routes and journey times for your trip
                        </p>

                        {plan.cost_breakdown.connectivity_suggestions && plan.cost_breakdown.connectivity_suggestions.length > 0 ? (
                          <div className="space-y-6">
                            {plan.cost_breakdown.connectivity_suggestions.map((conn, idx) => (
                              <div key={idx} className="p-5 bg-secondary/30 rounded-xl border border-border">
                                <div className="flex items-start justify-between mb-4">
                                  <div>
                                    <h5 className="font-bold text-lg capitalize flex items-center gap-2">
                                      {conn.transport_mode === 'flight' ? '✈️' : '🚆'} {conn.transport_mode}
                                    </h5>
                                    <p className="text-sm text-muted-foreground mt-1">
                                      {conn.from_location} → {conn.to_location}
                                    </p>
                                  </div>
                                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${conn.has_direct_connectivity ? 'bg-green-500/20 text-green-700 dark:text-green-400' : 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400'}`}>
                                    {conn.has_direct_connectivity ? '✓ Direct' : '⚠ Via Nearest'}
                                  </div>
                                </div>

                                <div className="grid md:grid-cols-2 gap-4 mb-4">
                                  <div className="p-3 bg-background rounded-lg">
                                    <p className="text-xs text-muted-foreground mb-1">Journey Time</p>
                                    <p className="font-heading text-xl font-bold text-primary">⏱️ {conn.journey_time_estimate}</p>
                                  </div>

                                  {!conn.has_direct_connectivity && conn.nearest_station_airport && (
                                    <div className="p-3 bg-background rounded-lg">
                                      <p className="text-xs text-muted-foreground mb-1">Nearest Station/Airport</p>
                                      <p className="font-medium">{conn.nearest_station_airport}</p>
                                      {conn.distance_to_nearest_km && (
                                        <p className="text-xs text-muted-foreground mt-1">📍 ~{conn.distance_to_nearest_km} km away</p>
                                      )}
                                    </div>
                                  )}
                                </div>

                                <div className="p-3 bg-background rounded-lg mb-4">
                                  <p className="text-sm text-muted-foreground mb-1">📋 Connectivity Notes</p>
                                  <p className="text-sm">{conn.connectivity_notes}</p>
                                </div>

                                {conn.suggested_options && conn.suggested_options.length > 0 && (
                                  <div>
                                    <p className="text-sm font-medium mb-2">Suggested Options:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {conn.suggested_options.map((option, oidx) => (
                                        <span key={oidx} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm border border-primary/20">
                                          {option}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-muted-foreground text-center py-8">
                            Connectivity suggestions will be included in your trip plan
                          </p>
                        )}
                      </div>
                    </div>
                  </TabsContent>

                  {/* Itinerary Tab */}
                  <TabsContent value="itinerary">
                    <ScrollArea className="h-[500px] pr-4">
                      <div className="space-y-4">
                        {plan.itinerary.map((day) => (
                          <div
                            key={day.day}
                            className="bg-card border border-border rounded-xl p-6"
                            data-testid={`day-${day.day}`}
                          >
                            <div className="flex items-center justify-between mb-4">
                              <div>
                                <h4 className="font-heading text-lg font-bold">
                                  Day {day.day}
                                </h4>
                                <p className="text-sm text-muted-foreground">
                                  {format(new Date(day.date), "EEEE, MMM d")}
                                </p>
                              </div>
                              {day.weather && (
                                <div className="text-right">
                                  <div className="flex items-center gap-2 text-sm">
                                    <CloudSun className="w-4 h-4 text-primary" />
                                    <span>{day.weather.weather_description}</span>
                                  </div>
                                  <p className="text-xs text-muted-foreground">
                                    {day.weather.temperature_min}° - {day.weather.temperature_max}°C
                                  </p>
                                </div>
                              )}
                            </div>

                            <div className="space-y-3">
                              {day.activities.map((activity, idx) => (
                                <div
                                  key={idx}
                                  className="flex gap-4 p-3 bg-secondary/30 rounded-lg"
                                >
                                  <div className="text-sm font-medium text-primary w-16 shrink-0">
                                    {activity.time}
                                  </div>
                                  <div className="flex-1">
                                    <p className="font-medium">{activity.activity}</p>
                                    <p className="text-sm text-muted-foreground">
                                      {activity.description}
                                    </p>
                                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                      <span>{activity.duration}</span>
                                      <span className="text-primary font-medium">
                                        {getCurrencySymbol(plan.cost_breakdown.currency)}
                                        {activity.cost}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>

                            {day.tips && (
                              <p className="mt-4 text-sm text-muted-foreground italic">
                                💡 {day.tips}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </TabsContent>

                  {/* Activities Tab - NEW */}
                  <TabsContent value="activities">
                    <div className="space-y-4">
                      <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                          <Activity className="w-5 h-5 text-primary" />
                          Activities Breakdown
                        </h4>
                        <p className="text-sm text-muted-foreground mb-6">
                          Cost breakdown by activity category for your trip
                        </p>

                        {plan.cost_breakdown.activities_breakdown && plan.cost_breakdown.activities_breakdown.length > 0 ? (
                          <div className="grid gap-4">
                            {plan.cost_breakdown.activities_breakdown.map((category, idx) => {
                              // Icon mapping for categories
                              const categoryIcons = {
                                adventure: Activity,
                                dining: Utensils,
                                cultural: Hotel,
                                relaxation: CloudSun,
                                nature: MapPin,
                                shopping: Package,
                                nightlife: Sparkles,
                                photography: Heart
                              };
                              const CategoryIcon = categoryIcons[category.category] || Activity;

                              return (
                                <div key={idx} className="p-4 bg-secondary/30 rounded-xl">
                                  <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                      <div className="p-2 bg-primary/10 rounded-lg">
                                        <CategoryIcon className="w-5 h-5 text-primary" />
                                      </div>
                                      <div>
                                        <h5 className="font-bold capitalize">{category.category}</h5>
                                        <p className="text-xs text-muted-foreground">{category.activities.length} activities</p>
                                      </div>
                                    </div>
                                    <span className="font-heading text-xl font-bold text-primary">
                                      {getCurrencySymbol(plan.cost_breakdown.currency)}{category.cost.toLocaleString()}
                                    </span>
                                  </div>

                                  <div className="mt-3 flex flex-wrap gap-2">
                                    {category.activities.map((activity, aidx) => (
                                      <span key={aidx} className="text-sm bg-background px-3 py-1 rounded-full border border-border">
                                        {activity}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <p className="text-muted-foreground text-center py-8">
                            Activities breakdown will be available in your trip plan
                          </p>
                        )}
                      </div>
                    </div>
                  </TabsContent>

                  {/* Tips Tab */}
                  <TabsContent value="tips">
                    <div className="bg-card border border-border rounded-xl p-6">
                      <h4 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-primary" />
                        Travel Tips
                      </h4>
                      <ul className="space-y-3">
                        {plan.travel_tips.map((tip, idx) => (
                          <li key={idx} className="flex gap-3">
                            <span className="text-primary">•</span>
                            <span className="text-muted-foreground">{tip}</span>
                          </li>
                        ))}
                      </ul>

                      <h4 className="font-heading text-lg font-bold mt-8 mb-4 flex items-center gap-2">
                        <Heart className="w-5 h-5 text-primary" />
                        Local Customs
                      </h4>
                      <ul className="space-y-3">
                        {plan.local_customs.map((custom, idx) => (
                          <li key={idx} className="flex gap-3">
                            <span className="text-primary">•</span>
                            <span className="text-muted-foreground">{custom}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </TabsContent>

                  {/* Packing Tab */}
                  <TabsContent value="packing">
                    <div className="bg-card border border-border rounded-xl p-6">
                      <h4 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                        <Package className="w-5 h-5 text-primary" />
                        Packing List
                      </h4>

                      {plan.packing_suggestions_detailed && plan.packing_suggestions_detailed.length > 0 ? (
                        <div className="space-y-6">
                          {plan.packing_suggestions_detailed.map((category, idx) => (
                            <div key={idx} className="space-y-3">
                              <h5 className="font-bold capitalize text-primary flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-primary"></span>
                                {category.category}
                              </h5>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-4">
                                {category.items.map((item, iidx) => (
                                  <div
                                    key={iidx}
                                    className="flex items-center gap-2 p-2 bg-secondary/30 rounded-lg"
                                  >
                                    <Checkbox />
                                    <span className="text-sm">{item}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="grid grid-cols-2 gap-2">
                          {plan.packing_suggestions.map((item, idx) => (
                            <div
                              key={idx}
                              className="flex items-center gap-2 p-2 bg-secondary/30 rounded-lg"
                            >
                              <Checkbox />
                              <span className="text-sm">{item}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </TabsContent>

                  {/* Info Tab */}
                  <TabsContent value="info">
                    <div className="space-y-4">
                      <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                          <CloudSun className="w-5 h-5 text-primary" />
                          Best Time to Visit
                        </h4>
                        <p className="text-muted-foreground">{plan.best_time_to_visit}</p>
                      </div>

                      <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                          <CloudSun className="w-5 h-5 text-primary" />
                          Weather Summary
                        </h4>
                        <p className="text-muted-foreground">{plan.weather_summary}</p>
                      </div>

                      <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4 flex items-center gap-2">
                          <Phone className="w-5 h-5 text-destructive" />
                          Emergency Contacts
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(plan.emergency_contacts).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="capitalize text-muted-foreground">{key}</span>
                              <span className="font-mono">{value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default TripPlanner;
