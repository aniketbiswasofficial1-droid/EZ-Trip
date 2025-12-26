import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";

const UsernameSetupModal = ({ isOpen, onClose }) => {
    const { user, refreshUser } = useAuth();
    const [username, setUsername] = useState("");
    const [usernameError, setUsernameError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleUsernameChange = (e) => {
        const val = e.target.value.toLowerCase();
        setUsername(val);

        // Validate format
        if (val && !/^[a-z0-9_-]{3,20}$/.test(val)) {
            setUsernameError("Username must be 3-20 characters (letters, numbers, _, -)");
        } else {
            setUsernameError("");
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!username || usernameError) {
            toast.error("Please enter a valid username");
            return;
        }

        setIsSubmitting(true);

        try {
            await axios.put(
                `${API}/auth/me/username`,
                { username },
                { withCredentials: true }
            );

            await refreshUser();
            toast.success("Username set successfully! 🎉");
            onClose();
        } catch (error) {
            console.error("Error setting username:", error);
            toast.error(error.response?.data?.detail || "Failed to set username");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSkip = () => {
        // Store that user skipped this session
        sessionStorage.setItem("username_setup_skipped", "true");
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[500px]" onPointerDownOutside={(e) => e.preventDefault()}>
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-2xl">
                        <Sparkles className="w-6 h-6 text-primary" />
                        Set Your Username
                    </DialogTitle>
                    <DialogDescription>
                        Choose a unique username to make it easier for friends to find and add you to trips!
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4 pt-4">
                    <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input
                            id="username"
                            placeholder="john_doe"
                            value={username}
                            onChange={handleUsernameChange}
                            autoFocus
                            required
                        />
                        {usernameError && (
                            <p className="text-sm text-destructive">{usernameError}</p>
                        )}
                        <p className="text-xs text-muted-foreground">
                            Your unique @username for easy discovery. You can change this later in your profile.
                        </p>
                    </div>

                    <div className="flex gap-2 pt-2">
                        <Button
                            type="submit"
                            className="flex-1 rounded-full font-bold btn-glow"
                            disabled={isSubmitting || !username || !!usernameError}
                        >
                            {isSubmitting ? "Setting..." : "Set Username"}
                        </Button>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleSkip}
                            className="rounded-full"
                        >
                            Skip for now
                        </Button>
                    </div>

                    <div className="bg-primary/10 border border-primary/30 rounded-lg p-3">
                        <p className="text-sm">
                            💡 <strong>Why set a username?</strong>
                            <br />
                            Friends can find you by @username instead of remembering your email!
                        </p>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default UsernameSetupModal;
