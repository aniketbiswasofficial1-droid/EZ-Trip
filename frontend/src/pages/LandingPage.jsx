import { useAuth } from "@/App";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { 
  Receipt, 
  Users, 
  RefreshCw, 
  Globe, 
  ArrowRight,
  Wallet,
  PieChart,
  Shield
} from "lucide-react";

const LandingPage = () => {
  const { user, login, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard');
    }
  }, [user, loading, navigate]);

  const features = [
    {
      icon: Receipt,
      title: "Smart Expense Tracking",
      description: "Add expenses with multiple payers and custom splits. Never lose track of who paid what."
    },
    {
      icon: RefreshCw,
      title: "Easy Refunds",
      description: "Handle refunds seamlessly. Clear indication of what refund is for and automatic balance updates."
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
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Google sign-in for security. Your financial data stays safe and private."
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
          <Button 
            onClick={login}
            className="rounded-full font-bold tracking-wide btn-glow"
            data-testid="header-login-btn"
          >
            Sign in with Google
          </Button>
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
                <span className="text-sm text-muted-foreground">Free forever for personal use</span>
              </div>
              
              <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1]">
                Split expenses,
                <br />
                <span className="text-primary">not friendships</span>
              </h1>
              
              <p className="text-lg text-muted-foreground max-w-lg">
                The modern way to track and split trip expenses. Handle complex splits, 
                manage refunds, and settle up with friends in any currency.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  onClick={login}
                  size="lg"
                  className="rounded-full font-bold tracking-wide btn-glow text-lg px-8 py-6"
                  data-testid="hero-get-started-btn"
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
                  <p className="text-sm text-muted-foreground">Google Auth</p>
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
                        <p className="text-sm text-muted-foreground">Paid by Alex</p>
                      </div>
                      <p className="font-heading text-xl font-bold">$420</p>
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
                        <p className="text-sm text-muted-foreground">Paid by Sarah</p>
                      </div>
                      <div className="text-right">
                        <p className="font-heading text-xl font-bold">$85</p>
                        <p className="text-xs text-primary">$15 refunded</p>
                      </div>
                    </div>
                  </div>

                  {/* Balance summary */}
                  <div className="pt-4 border-t border-border">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Your balance</span>
                      <span className="font-heading text-2xl font-bold text-primary">+$52.50</span>
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
                className="bg-card border border-border rounded-xl p-6 card-hover animate-fade-in opacity-0"
              >
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-heading text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Native Ad Slot Example */}
      <section className="py-16 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-card border border-border rounded-xl p-6 card-hover relative">
            <span className="absolute top-4 right-4 bg-white/10 text-xs px-2 py-1 rounded uppercase tracking-widest text-muted-foreground">
              Sponsored
            </span>
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 bg-secondary rounded-xl flex items-center justify-center shrink-0">
                <Globe className="w-10 h-10 text-muted-foreground" />
              </div>
              <div>
                <h3 className="font-heading text-xl font-bold mb-1">Travel Insurance</h3>
                <p className="text-muted-foreground">Protect your next adventure with comprehensive travel coverage starting at $9/trip.</p>
              </div>
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
            onClick={login}
            size="lg"
            className="rounded-full font-bold tracking-wide btn-glow text-lg px-8 py-6"
            data-testid="cta-get-started-btn"
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
    </div>
  );
};

export default LandingPage;
