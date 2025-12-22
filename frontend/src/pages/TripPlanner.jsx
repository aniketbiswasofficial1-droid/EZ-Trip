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
  Plane,
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
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState(addDays(new Date(), 7));
  const [endDate, setEndDate] = useState(addDays(new Date(), 14));
  const [numTravelers, setNumTravelers] = useState(2);
  const [budgetPreference, setBudgetPreference] = useState("moderate");
  const [interests, setInterests] = useState([]);
  const [accommodationType, setAccommodationType] = useState("hotel");
  const [includeFlights, setIncludeFlights] = useState(true);
  const [departureCity, setDepartureCity] = useState("");

  const handleInterestToggle = (interestId) => {
    setInterests((prev) =>
      prev.includes(interestId)
        ? prev.filter((i) => i !== interestId)
        : [...prev, interestId]
    );
  };

  const handleGeneratePlan = async () => {
    const newErrors = {};
    
    if (!destination.trim()) {
      newErrors.destination = "Please enter a destination";
    }

    if (!startDate || !endDate) {
      newErrors.dates = "Please select travel dates";
    }

    if (startDate && endDate && startDate > endDate) {
      newErrors.dates = "End date must be after start date";
    }

    if (includeFlights && !departureCity.trim()) {
      newErrors.departureCity = "Please enter your departure city";
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
          destination,
          start_date: format(startDate, "yyyy-MM-dd"),
          end_date: format(endDate, "yyyy-MM-dd"),
          num_travelers: numTravelers,
          budget_preference: budgetPreference,
          interests,
          accommodation_type: accommodationType,
          include_flights: includeFlights,
          departure_city: includeFlights ? departureCity : null,
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
      await axios.post(`${API}/planner/save`, plan, { withCredentials: true });
      toast.success("Trip plan saved!");
    } catch (error) {
      console.error("Error saving plan:", error);
      toast.error("Failed to save plan");
    } finally {
      setSaving(false);
    }
  };

  const getCurrencySymbol = (currency) => {
    const symbols = { USD: "$", EUR: "€", GBP: "£", INR: "₹" };
    return symbols[currency] || currency;
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

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
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

            <div className="bg-card border border-border rounded-xl p-6 space-y-6 animate-slide-up">
              {/* Destination */}
              <div className="space-y-2">
                <Label htmlFor="destination">Where do you want to go?</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="destination"
                    placeholder="Paris, France"
                    value={destination}
                    onChange={(e) => {
                      setDestination(e.target.value);
                      if (errors.destination) setErrors({...errors, destination: null});
                    }}
                    className={`pl-10 h-12 ${errors.destination ? 'border-destructive' : ''}`}
                    data-testid="destination-input"
                  />
                </div>
                {errors.destination && (
                  <p className="text-sm text-destructive">{errors.destination}</p>
                )}
              </div>

              {/* Date Range - Separate Inputs */}
              <div className="space-y-2">
                <Label>When are you traveling?</Label>
                <div className="grid grid-cols-2 gap-4">
                  {/* Start Date */}
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
                            // Auto-adjust end date if needed
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

                  {/* End Date */}
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

              {/* Travelers */}
              <div className="space-y-2">
                <Label>Number of travelers</Label>
                <div className="flex items-center gap-4">
                  <Users className="w-5 h-5 text-muted-foreground" />
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={numTravelers}
                    onChange={(e) => setNumTravelers(parseInt(e.target.value) || 1)}
                    className="w-24 h-12"
                    data-testid="travelers-input"
                  />
                  <span className="text-muted-foreground">
                    {numTravelers === 1 ? "traveler" : "travelers"}
                  </span>
                </div>
              </div>

              {/* Budget */}
              <div className="space-y-2">
                <Label>Budget preference</Label>
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
                <Label>Accommodation type</Label>
                <Select value={accommodationType} onValueChange={setAccommodationType}>
                  <SelectTrigger className="h-12" data-testid="accommodation-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hostel">Hostel</SelectItem>
                    <SelectItem value="hotel">Hotel</SelectItem>
                    <SelectItem value="airbnb">Airbnb/Vacation Rental</SelectItem>
                    <SelectItem value="resort">Resort</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Flights */}
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Checkbox
                    checked={includeFlights}
                    onCheckedChange={setIncludeFlights}
                    data-testid="include-flights-checkbox"
                  />
                  <Label className="cursor-pointer">Include flight estimates</Label>
                </div>
                {includeFlights && (
                  <div className="relative animate-fade-in">
                    <Plane className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <Input
                      placeholder="Departure city (e.g., New York)"
                      value={departureCity}
                      onChange={(e) => {
                        setDepartureCity(e.target.value);
                        if (errors.departureCity) setErrors({...errors, departureCity: null});
                      }}
                      className={`pl-10 h-12 ${errors.departureCity ? 'border-destructive' : ''}`}
                      data-testid="departure-city-input"
                    />
                    {errors.departureCity && (
                      <p className="text-sm text-destructive mt-1">{errors.departureCity}</p>
                    )}
                  </div>
                )}
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
                        className={`flex items-center gap-2 p-3 rounded-lg border transition-all ${
                          isSelected
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
                    <DollarSign className="w-5 h-5 text-primary" />
                    Cost Estimate
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
                    {[
                      { label: "Flights", value: plan.cost_breakdown.flights, icon: Plane },
                      { label: "Accommodation", value: plan.cost_breakdown.accommodation, icon: Hotel },
                      { label: "Food", value: plan.cost_breakdown.food, icon: Utensils },
                      { label: "Activities", value: plan.cost_breakdown.activities, icon: Activity },
                      { label: "Transport", value: plan.cost_breakdown.transportation, icon: Car },
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
                  <TabsList className="bg-secondary/50 p-1 rounded-full w-full grid grid-cols-5">
                    <TabsTrigger value="itinerary" className="rounded-full text-xs sm:text-sm">
                      Itinerary
                    </TabsTrigger>
                    <TabsTrigger value="prices" className="rounded-full text-xs sm:text-sm">
                      Prices
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
