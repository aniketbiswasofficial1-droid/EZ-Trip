import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/App";
import { toast } from "sonner";
import { Wallet, Eye, EyeOff, Check, X } from "lucide-react";
import { GoogleLogin } from '@react-oauth/google';

const AuthModal = ({ isOpen, onClose, defaultTab = "login" }) => {
  const { loginWithPassword, loginWithGoogle, register } = useAuth();
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [isLoading, setIsLoading] = useState(false);

  // Visibility States
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Form States
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    username: "",  // NEW: Username field
    password: "",
    confirmPassword: ""
  });

  const [passwordError, setPasswordError] = useState("");
  const [usernameError, setUsernameError] = useState("");  // NEW: Username validation

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });

    // Real-time validation for registration
    if (activeTab === "register" && e.target.name === "password") {
      validatePasswordStrength(e.target.value);
    }
  };

  const validatePasswordStrength = (password) => {
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    const isValidLength = password.length >= 8;

    if (!isValidLength || !hasLetter || !hasNumber || !hasSpecial) {
      setPasswordError("Password must be 8+ chars, include letters, numbers & special chars.");
      return false;
    }
    setPasswordError("");
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (activeTab === "login") {
        await loginWithPassword(formData.email, formData.password);
        onClose();
      } else {
        // Registration Validations
        if (!validatePasswordStrength(formData.password)) {
          toast.error("Password is too weak");
          setIsLoading(false);
          return;
        }

        if (formData.password !== formData.confirmPassword) {
          toast.error("Passwords do not match");
          setIsLoading(false);
          return;
        }

        await register(formData.name, formData.email, formData.username, formData.password);
        onClose();
      }
    } catch (error) {
      const msg = error.response?.data?.detail || "Authentication failed";
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setIsLoading(true);
    try {
      await loginWithGoogle(credentialResponse.credential);
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Google sign-in failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleError = () => {
    toast.error("Google sign-in failed");
  };

  const togglePasswordVisibility = () => setShowPassword(!showPassword);
  const toggleConfirmVisibility = () => setShowConfirmPassword(!showConfirmPassword);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] bg-card border-border">
        <DialogHeader>
          <DialogTitle className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
              <Wallet className="w-6 h-6 text-primary" />
            </div>
            <span className="font-heading text-xl">Welcome to EZ Trip</span>
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(val) => {
          setActiveTab(val);
          setFormData({ name: "", email: "", username: "", password: "", confirmPassword: "" });
          setPasswordError("");
          setUsernameError("");
        }} className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="login">Log In</TabsTrigger>
            <TabsTrigger value="register">Sign Up</TabsTrigger>
          </TabsList>

          <form onSubmit={handleSubmit} className="space-y-4">
            {activeTab === "register" && (
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  name="name"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
            )}

            {activeTab === "register" && (
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  name="username"
                  placeholder="john_doe"
                  value={formData.username}
                  onChange={(e) => {
                    const val = e.target.value.toLowerCase();
                    setFormData({ ...formData, username: val });
                    // Validate username format
                    if (val && !/^[a-z0-9_-]{3,20}$/.test(val)) {
                      setUsernameError("Username must be 3-20 characters (letters, numbers, _, -)");
                    } else {
                      setUsernameError("");
                    }
                  }}
                  required
                />
                {usernameError && (
                  <p className="text-xs text-destructive">{usernameError}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Your unique @username for easy discovery
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="hello@example.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={togglePasswordVisibility}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
              {activeTab === "register" && passwordError && (
                <p className="text-xs text-destructive">{passwordError}</p>
              )}
            </div>

            {activeTab === "register" && (
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    className="pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={toggleConfirmVisibility}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                </div>
              </div>
            )}

            <Button type="submit" className="w-full font-bold" disabled={isLoading}>
              {isLoading ? "Processing..." : (activeTab === "login" ? "Sign In" : "Create Account")}
            </Button>
          </form>

          {/* Google Sign-In */}
          <div className="mt-4">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>

            <div className="mt-4">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                theme="outline"
                size="large"
                text={activeTab === "login" ? "signin_with" : "signup_with"}
                width="100%"
                logo_alignment="left"
                type="standard"
                shape="rectangular"
              />
            </div>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;