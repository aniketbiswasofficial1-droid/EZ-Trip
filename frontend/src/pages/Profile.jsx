import { useState, useEffect, useRef } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Wallet,
    ArrowLeft,
    User,
    Lock,
    Upload,
    LogOut,
    Sparkles,
    Plus,
    Shield,
    Loader2,
    Camera,
} from "lucide-react";

const Profile = () => {
    const { user, logout, refreshUser } = useAuth();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [isAdmin, setIsAdmin] = useState(false);
    const fileInputRef = useRef(null);

    // Profile form state
    const [name, setName] = useState(user?.name || "");
    const [dateOfBirth, setDateOfBirth] = useState(user?.date_of_birth || "");
    const [profilePicture, setProfilePicture] = useState(user?.picture || "");

    // Password form state
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [changingPassword, setChangingPassword] = useState(false);

    useEffect(() => {
        if (user) {
            setName(user.name || "");
            setDateOfBirth(user.date_of_birth || "");
            setProfilePicture(user.picture || "");
        }
        checkAdminStatus();
    }, [user]);

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

    const handleProfilePictureUpload = async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            toast.error("File too large. Maximum size is 5MB");
            return;
        }

        // Validate file type
        const validTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
        if (!validTypes.includes(file.type)) {
            toast.error("Invalid file type. Please use JPEG, PNG, GIF, or WebP");
            return;
        }

        setUploading(true);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const uploadResponse = await axios.post(
                `${API}/auth/upload-profile-picture`,
                formData,
                {
                    withCredentials: true,
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            // Construct full URL from the backend URL
            const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
            const imageUrl = `${BACKEND_URL}${uploadResponse.data.url}`;

            // Update profile with new picture
            await axios.put(
                `${API}/auth/me`,
                { custom_profile_picture: imageUrl },
                { withCredentials: true }
            );

            setProfilePicture(imageUrl);
            await refreshUser();
            toast.success("Profile picture updated!");
        } catch (error) {
            console.error("Error uploading picture:", error);
            toast.error(error.response?.data?.detail || "Failed to upload picture");
        } finally {
            setUploading(false);
        }
    };

    const handleSaveProfile = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            await axios.put(
                `${API}/auth/me`,
                {
                    name,
                    date_of_birth: dateOfBirth || null,
                },
                { withCredentials: true }
            );

            await refreshUser();
            toast.success("Profile updated successfully!");
        } catch (error) {
            console.error("Error updating profile:", error);
            toast.error("Failed to update profile");
        } finally {
            setLoading(false);
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();

        if (newPassword !== confirmPassword) {
            toast.error("New passwords don't match");
            return;
        }

        if (newPassword.length < 8) {
            toast.error("Password must be at least 8 characters long");
            return;
        }

        setChangingPassword(true);

        try {
            await axios.post(
                `${API}/auth/change-password`,
                {
                    current_password: currentPassword,
                    new_password: newPassword,
                },
                { withCredentials: true }
            );

            toast.success("Password changed successfully!");
            setCurrentPassword("");
            setNewPassword("");
            setConfirmPassword("");
        } catch (error) {
            console.error("Error changing password:", error);
            toast.error(
                error.response?.data?.detail || "Failed to change password"
            );
        } finally {
            setChangingPassword(false);
        }
    };

    const isOAuthUser = user?.oauth_provider;

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
                            <Wallet className="w-8 h-8 text-primary" />
                            <span className="font-heading text-xl font-bold tracking-tight">
                                EZ Trip
                            </span>
                        </div>
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
                            <DropdownMenuItem onClick={() => navigate("/planner")}>
                                <Sparkles className="w-4 h-4 mr-2" />
                                AI Trip Planner
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                                <Plus className="w-4 h-4 mr-2" />
                                Create New Trip
                            </DropdownMenuItem>
                            {isAdmin && (
                                <DropdownMenuItem onClick={() => navigate("/admin")}>
                                    <Shield className="w-4 h-4 mr-2" />
                                    Admin Panel
                                </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                onClick={logout}
                                className="text-destructive focus:text-destructive"
                            >
                                <LogOut className="w-4 h-4 mr-2" />
                                Sign Out
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-6 py-8">
                <div className="mb-8 animate-fade-in">
                    <h1 className="font-heading text-4xl font-bold mb-2">
                        Profile Settings
                    </h1>
                    <p className="text-muted-foreground">
                        Manage your profile information and security settings
                    </p>
                </div>

                <Tabs defaultValue="profile" className="space-y-6">
                    <TabsList className="bg-secondary/50 p-1 rounded-full">
                        <TabsTrigger value="profile" className="rounded-full">
                            <User className="w-4 h-4 mr-2" />
                            Profile
                        </TabsTrigger>
                        <TabsTrigger
                            value="security"
                            className="rounded-full"
                            disabled={isOAuthUser}
                        >
                            <Lock className="w-4 h-4 mr-2" />
                            Security
                        </TabsTrigger>
                    </TabsList>

                    {isOAuthUser && (
                        <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
                            <p className="text-sm">
                                🔒 <strong>Password management unavailable</strong>
                                <br />
                                You signed in with <strong>Google</strong>. Password changes are managed through your Google account settings.
                            </p>
                        </div>
                    )}

                    {/* Profile Tab */}
                    <TabsContent value="profile" className="space-y-6">
                        <div className="bg-card border border-border rounded-xl p-6 animate-slide-up">
                            <h2 className="font-heading text-xl font-bold mb-6">
                                Profile Information
                            </h2>

                            <form onSubmit={handleSaveProfile} className="space-y-6">
                                {/* Profile Picture */}
                                <div className="flex flex-col items-center gap-4">
                                    <div className="relative">
                                        <Avatar className="w-32 h-32">
                                            <AvatarImage src={profilePicture} />
                                            <AvatarFallback className="text-4xl">
                                                {name?.charAt(0) || "U"}
                                            </AvatarFallback>
                                        </Avatar>
                                        <Button
                                            type="button"
                                            size="icon"
                                            className="absolute bottom-0 right-0 rounded-full"
                                            onClick={() => fileInputRef.current?.click()}
                                            disabled={uploading}
                                        >
                                            {uploading ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Camera className="w-4 h-4" />
                                            )}
                                        </Button>
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            accept="image/jpeg,image/png,image/gif,image/webp"
                                            onChange={handleProfilePictureUpload}
                                            className="hidden"
                                        />
                                    </div>
                                    <p className="text-sm text-muted-foreground text-center">
                                        Click the camera icon to upload a new picture
                                        <br />
                                        Max 5MB • JPEG, PNG, GIF, or WebP
                                    </p>
                                </div>

                                {/* Name */}
                                <div className="space-y-2">
                                    <Label htmlFor="name">Name</Label>
                                    <Input
                                        id="name"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        placeholder="Your name"
                                        className="h-12"
                                    />
                                </div>

                                {/* Email (read-only) */}
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        value={user?.email || ""}
                                        disabled
                                        className="h-12 bg-secondary/50"
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        Email cannot be changed
                                    </p>
                                </div>

                                {/* Date of Birth */}
                                <div className="space-y-2">
                                    <Label htmlFor="dob">Date of Birth</Label>
                                    <Input
                                        id="dob"
                                        type="date"
                                        value={dateOfBirth}
                                        onChange={(e) => setDateOfBirth(e.target.value)}
                                        className="h-12"
                                    />
                                </div>

                                {isOAuthUser && (
                                    <div className="bg-secondary/30 border border-border rounded-lg p-4">
                                        <p className="text-sm text-muted-foreground">
                                            📱 Signed in with {user.oauth_provider}
                                        </p>
                                    </div>
                                )}

                                <Button
                                    type="submit"
                                    className="w-full h-12 rounded-full font-bold btn-glow"
                                    disabled={loading}
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        "Save Changes"
                                    )}
                                </Button>
                            </form>
                        </div>
                    </TabsContent>

                    {/* Security Tab */}
                    <TabsContent value="security" className="space-y-6">
                        <div className="bg-card border border-border rounded-xl p-6 animate-slide-up">
                            <h2 className="font-heading text-xl font-bold mb-6">
                                Change Password
                            </h2>

                            <form onSubmit={handleChangePassword} className="space-y-6">
                                <div className="space-y-2">
                                    <Label htmlFor="current-password">Current Password</Label>
                                    <Input
                                        id="current-password"
                                        type="password"
                                        value={currentPassword}
                                        onChange={(e) => setCurrentPassword(e.target.value)}
                                        placeholder="Enter current password"
                                        className="h-12"
                                        required
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="new-password">New Password</Label>
                                    <Input
                                        id="new-password"
                                        type="password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        placeholder="Enter new password"
                                        className="h-12"
                                        required
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        Must be at least 8 characters with letters, numbers, and
                                        special characters
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="confirm-password">Confirm New Password</Label>
                                    <Input
                                        id="confirm-password"
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        placeholder="Confirm new password"
                                        className="h-12"
                                        required
                                    />
                                </div>

                                <Button
                                    type="submit"
                                    className="w-full h-12 rounded-full font-bold btn-glow"
                                    disabled={changingPassword}
                                >
                                    {changingPassword ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Changing Password...
                                        </>
                                    ) : (
                                        "Change Password"
                                    )}
                                </Button>
                            </form>
                        </div>
                    </TabsContent>
                </Tabs>
            </main>
        </div>
    );
};

export default Profile;
