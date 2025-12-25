import { useAuth } from "@/App";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import AuthModal from "@/components/AuthModal";
import {
  Receipt,
  Users,
  RefreshCw,
  Globe,
  ArrowRight,
  Wallet,
  PieChart,
  Shield,
  Sparkles,
  MapPin
} from "lucide-react";

const LandingPage = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [initialAuthTab, setInitialAuthTab] = useState("login"); // 'login' or 'register'

  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard');
    }
  }, [user, loading, navigate]);

  const openAuth = (tab) => {
    setInitialAuthTab(tab);
    setIsAuthOpen(true);
  };

  const features = [
    {
      icon: Sparkles,
      title: "AI Trip Planner",
      description: "Let AI create your perfect itinerary. Get personalized recommendations for activities, restaurants, and attractions.",
      highlight: true
    },
    {
      icon: Receipt,
      title: "Smart Expense Tracking",
      description: "Add expenses with multiple payers and custom splits. Never lose track of who paid what."
    },
    {
      icon: RefreshCw,
      title: "Easy Refunds & Settlements",
      description: "Handle refunds and record payments seamlessly. Clear tracking of who owes whom with automatic balance updates."
    },
    {
      icon: Globe,
      title: "Multi-Currency",
      description: "Support for 13+ currencies. Perfect for international trips with friends."
    },
    {
      icon: Users,
      title: "Group Management",
      description: "Create trips, add friends, and manage expenses together. Everyone stays in sync."
    },
    {
      icon: PieChart,
      title: "Smart Settlements",
      description: "Automatic calculation of who owes whom. Minimize the number of transactions needed."
    }
  ];

  return (
    <div className="min-h-screen bg-background relative z-10">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wallet className="w-8 h-8 text-primary" />
            <span className="font-heading text-xl font-bold tracking-tight">EZ Trip</span>
          </div>

          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={() => openAuth('login')}
              className="font-bold hover:text-primary"
            >
              Log In
            </Button>
            <Button
              onClick={() => openAuth('register')}
              className="rounded-full font-bold tracking-wide btn-glow"
            >
              Sign Up
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left Content */}
            <div className="space-y-8 animate-fade-in">
              <div className="inline-flex items-center gap-2 bg-secondary/50 px-4 py-2 rounded-full border border-border">
                <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
                <span className="text-sm text-muted-foreground">Free for personal use</span>
              </div>

              <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]">
                Split expenses,
                <br />
                <span className="text-primary">not friendships</span>
              </h1>

              <p className="text-lg text-muted-foreground max-w-lg">
                The modern way to track and split trip expenses. Handle complex splits,
                manage refunds, settle up with friends, and plan your perfect trip with AI - all in one place.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  onClick={() => openAuth('register')}
                  size="lg"
                  className="rounded-full font-bold tracking-wide btn-glow text-lg px-8 py-6"
                >
                  Get Started Free
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </div>

              <div className="flex items-center gap-8 pt-4">
                <div>
                  <p className="text-2xl font-heading font-bold text-primary">13+</p>
                  <p className="text-sm text-muted-foreground">Currencies</p>
                </div>
                <div className="w-px h-10 bg-border"></div>
                <div>
                  <p className="text-2xl font-heading font-bold text-primary">100%</p>
                  <p className="text-sm text-muted-foreground">Free</p>
                </div>
                <div className="w-px h-10 bg-border"></div>
                <div>
                  <p className="text-2xl font-heading font-bold text-primary">Secure</p>
                  <p className="text-sm text-muted-foreground">Private</p>
                </div>
              </div>
            </div>

            {/* Right Content - Visual */}
            <div className="relative animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <div className="relative bg-card border border-border rounded-2xl p-8 card-hover">
                <div className="absolute -top-4 -right-4 bg-primary text-primary-foreground px-4 py-2 rounded-full text-sm font-bold">
                  Example Trip
                </div>

                <h3 className="font-heading text-2xl font-bold mb-6">Beach Vacation</h3>

                <div className="space-y-4">
                  {/* Sample expense */}
                  <div className="bg-secondary/50 rounded-xl p-4 border border-border">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-medium">Hotel Booking</p>
                        <p className="text-sm text-muted-foreground">Paid by Rahul</p>
                      </div>
                      <p className="font-heading text-xl font-bold">₹15,000</p>
                    </div>
                    <div className="flex gap-2 mt-3">
                      <span className="text-xs bg-secondary px-2 py-1 rounded-full">Split: 3 people</span>
                    </div>
                  </div>

                  {/* Sample expense with refund */}
                  <div className="bg-secondary/50 rounded-xl p-4 border border-border">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="font-medium">Restaurant Dinner</p>
                        <p className="text-sm text-muted-foreground">Paid by Priya</p>
                      </div>
                      <div className="text-right">
                        <p className="font-heading text-xl font-bold">₹2,500</p>
                        <p className="text-xs text-primary">₹500 refunded</p>
                      </div>
                    </div>
                  </div>

                  {/* Balance summary */}
                  <div className="pt-4 border-t border-border">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Your balance</span>
                      <span className="font-heading text-2xl font-bold text-primary">+₹1,500</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">You are owed money</p>
                  </div>
                </div>
              </div>

              {/* Decorative elements */}
              <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-primary/5 rounded-full blur-3xl"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 bg-card/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 animate-fade-in">
            <h2 className="font-heading text-4xl sm:text-5xl font-bold mb-4">
              Everything you need to split expenses
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Powerful features designed to make expense splitting simple, fair, and transparent.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 stagger-children">
            {features.map((feature, index) => (
              <div
                key={index}
                className={`bg-card border rounded-xl p-6 card-hover animate-fade-in opacity-0 ${feature.highlight ? 'border-primary bg-primary/5' : 'border-border'
                  }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${feature.highlight ? 'bg-primary/20' : 'bg-primary/10'
                  }`}>
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-heading text-xl font-bold mb-2">
                  {feature.title}
                  {feature.highlight && (
                    <span className="ml-2 text-xs bg-primary text-primary-foreground px-2 py-1 rounded-full">NEW</span>
                  )}
                </h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Trip Planner Promotion */}
      <section className="py-24 px-6 bg-gradient-to-br from-primary/10 via-background to-background">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left - Content */}
            <div className="space-y-6 animate-fade-in">
              <div className="inline-flex items-center gap-2 bg-primary/10 px-4 py-2 rounded-full border border-primary/20">
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-primary">Powered by AI</span>
              </div>

              <h2 className="font-heading text-4xl sm:text-5xl font-bold">
                Plan your perfect trip with AI
              </h2>

              <p className="text-lg text-muted-foreground">
                Stop spending hours researching. Our AI Trip Planner creates personalized day-by-day itineraries
                with activities, restaurants, and attractions tailored to your preferences and budget.
              </p>

              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                    <MapPin className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Personalized Itineraries</p>
                    <p className="text-sm text-muted-foreground">Day-by-day plans customized to your style</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Smart Recommendations</p>
                    <p className="text-sm text-muted-foreground">AI-powered suggestions for activities and dining</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                    <Globe className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">Budget Friendly</p>
                    <p className="text-sm text-muted-foreground">Get cost estimates and booking links</p>
                  </div>
                </div>
              </div>

              <Button
                onClick={() => user ? navigate('/planner') : openAuth('register')}
                size="lg"
                className="rounded-full font-bold tracking-wide btn-glow text-lg px-8"
              >
                Try AI Trip Planner
                <Sparkles className="w-5 h-5 ml-2" />
              </Button>
            </div>

            {/* Right - Visual */}
            <div className="relative">
              <div className="bg-card border border-border rounded-2xl p-6 card-hover">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-heading font-bold">AI Trip Planner</p>
                    <p className="text-xs text-muted-foreground">Your personal travel assistant</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="bg-secondary/50 rounded-lg p-4">
                    <p className="text-sm font-medium mb-1">Day 1 - Arrival & Exploration</p>
                    <p className="text-xs text-muted-foreground">Morning: City walking tour • Lunch: Local cuisine • Evening: Rooftop bar</p>
                  </div>
                  <div className="bg-secondary/50 rounded-lg p-4">
                    <p className="text-sm font-medium mb-1">Day 2 - Cultural Experience</p>
                    <p className="text-xs text-muted-foreground">Visit museums • Traditional dinner • Night market</p>
                  </div>
                  <div className="bg-secondary/50 rounded-lg p-4">
                    <p className="text-sm font-medium mb-1">Day 3 - Adventure Day</p>
                    <p className="text-xs text-muted-foreground">Hiking trip • Beach time • Sunset viewing</p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-border">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Estimated Budget</span>
                    <span className="font-heading font-bold text-primary">₹25,000 - ₹40,000</span>
                  </div>
                </div>
              </div>

              {/* Decorative elements */}
              <div className="absolute -z-10 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-primary/5 rounded-full blur-3xl"></div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="font-heading text-4xl sm:text-5xl font-bold mb-6">
            Ready to simplify your group expenses?
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join thousands of travelers who trust EZ Trip for fair and easy expense splitting.
          </p>
          <Button
            onClick={() => openAuth('register')}
            size="lg"
            className="rounded-full font-bold tracking-wide btn-glow text-lg px-8 py-6"
          >
            Start Splitting Now
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-border">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Wallet className="w-6 h-6 text-primary" />
            <span className="font-heading font-bold">EZ Trip</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Split expenses, not friendships.
          </p>
        </div>
      </footer>

      {/* Auth Modal - Pass the initial tab state if your AuthModal supports it */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        defaultTab={initialAuthTab}
      />
    </div>
  );
};

export default LandingPage;