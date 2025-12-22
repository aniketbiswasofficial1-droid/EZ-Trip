import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Wallet,
  ArrowLeft,
  Plus,
  Users,
  Receipt,
  RefreshCw,
  Trash2,
  UserPlus,
  X,
  ArrowRight,
  Calendar,
  Globe,
  Pencil,
  Lock,
  Unlock,
} from "lucide-react";
import { format } from "date-fns";

const TripDetail = () => {
  const { tripId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [trip, setTrip] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);

  // Dialogs
  const [addExpenseOpen, setAddExpenseOpen] = useState(false);
  const [editExpenseOpen, setEditExpenseOpen] = useState(false);
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [addRefundOpen, setAddRefundOpen] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState(null);

  // New expense form
  const [newExpense, setNewExpense] = useState({
    description: "",
    total_amount: "",
    currency: "USD",
    category: "general",
    payers: [],
    splits: [],
  });
  
  // Multiple payers mode
  const [multiplePayersMode, setMultiplePayersMode] = useState(false);
  const [singlePayer, setSinglePayer] = useState("");

  // New member form
  const [newMember, setNewMember] = useState({ email: "", name: "" });

  // New refund form
  const [newRefund, setNewRefund] = useState({
    amount: "",
    reason: "",
    refunded_to: [],
  });

  useEffect(() => {
    fetchTrip();
    fetchExpenses();
    fetchBalances();
    fetchSettlements();
    fetchCurrencies();
  }, [tripId]);

  const fetchTrip = async () => {
    try {
      const response = await axios.get(`${API}/trips/${tripId}`, {
        withCredentials: true,
      });
      setTrip(response.data);
      setNewExpense((prev) => ({ ...prev, currency: response.data.currency }));
    } catch (error) {
      console.error("Error fetching trip:", error);
      toast.error("Failed to load trip");
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const fetchExpenses = async () => {
    try {
      const response = await axios.get(`${API}/expenses/trip/${tripId}`, {
        withCredentials: true,
      });
      setExpenses(response.data);
    } catch (error) {
      console.error("Error fetching expenses:", error);
    }
  };

  const fetchBalances = async () => {
    try {
      const response = await axios.get(`${API}/trips/${tripId}/balances`, {
        withCredentials: true,
      });
      setBalances(response.data);
    } catch (error) {
      console.error("Error fetching balances:", error);
    }
  };

  const fetchSettlements = async () => {
    try {
      const response = await axios.get(`${API}/trips/${tripId}/settlements`, {
        withCredentials: true,
      });
      setSettlements(response.data);
    } catch (error) {
      console.error("Error fetching settlements:", error);
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

  const getCurrencySymbol = (code) => {
    const currency = currencies.find((c) => c.code === code);
    return currency?.symbol || code;
  };

  // Handle expense creation
  const handleCreateExpense = async (e) => {
    e.preventDefault();

    if (!newExpense.description || !newExpense.total_amount) {
      toast.error("Please fill in all required fields");
      return;
    }

    // Build payers array based on mode
    let payersArray = [];
    if (multiplePayersMode) {
      payersArray = newExpense.payers.filter(p => p.amount > 0);
      if (payersArray.length === 0) {
        toast.error("Please enter amounts for payers");
        return;
      }
    } else {
      if (!singlePayer) {
        toast.error("Please select who paid");
        return;
      }
      payersArray = [{ user_id: singlePayer, amount: parseFloat(newExpense.total_amount) }];
    }

    if (newExpense.splits.length === 0) {
      toast.error("Please select at least one person to split with");
      return;
    }

    try {
      const payload = {
        trip_id: tripId,
        description: newExpense.description,
        total_amount: parseFloat(newExpense.total_amount),
        currency: newExpense.currency,
        category: newExpense.category,
        payers: payersArray,
        splits: newExpense.splits,
      };

      await axios.post(`${API}/expenses`, payload, { withCredentials: true });

      toast.success("Expense added successfully!");
      setAddExpenseOpen(false);
      resetExpenseForm();
      fetchExpenses();
      fetchBalances();
      fetchSettlements();
      fetchTrip();
    } catch (error) {
      console.error("Error creating expense:", error);
      toast.error("Failed to add expense");
    }
  };

  // Handle expense update
  const handleUpdateExpense = async (e) => {
    e.preventDefault();

    if (!newExpense.description || !newExpense.total_amount) {
      toast.error("Please fill in all required fields");
      return;
    }

    // Build payers array based on mode
    let payersArray = [];
    if (multiplePayersMode) {
      payersArray = newExpense.payers.filter(p => p.amount > 0);
      if (payersArray.length === 0) {
        toast.error("Please enter amounts for payers");
        return;
      }
    } else {
      if (!singlePayer) {
        toast.error("Please select who paid");
        return;
      }
      payersArray = [{ user_id: singlePayer, amount: parseFloat(newExpense.total_amount) }];
    }

    if (newExpense.splits.length === 0) {
      toast.error("Please select at least one person to split with");
      return;
    }

    try {
      const payload = {
        description: newExpense.description,
        total_amount: parseFloat(newExpense.total_amount),
        currency: newExpense.currency,
        category: newExpense.category,
        payers: payersArray,
        splits: newExpense.splits,
      };

      await axios.put(`${API}/expenses/${selectedExpense.expense_id}`, payload, { withCredentials: true });

      toast.success("Expense updated successfully!");
      setEditExpenseOpen(false);
      setSelectedExpense(null);
      resetExpenseForm();
      fetchExpenses();
      fetchBalances();
      fetchSettlements();
      fetchTrip();
    } catch (error) {
      console.error("Error updating expense:", error);
      toast.error("Failed to update expense");
    }
  };

  // Open edit expense dialog
  const openEditExpense = (expense) => {
    setSelectedExpense(expense);
    
    // Check if multiple payers
    const hasMultiplePayers = expense.payers.length > 1;
    setMultiplePayersMode(hasMultiplePayers);
    
    if (hasMultiplePayers) {
      setSinglePayer("");
    } else {
      setSinglePayer(expense.payers[0]?.user_id || "");
    }
    
    setNewExpense({
      description: expense.description,
      total_amount: expense.total_amount.toString(),
      currency: expense.currency,
      category: expense.category || "general",
      payers: expense.payers,
      splits: expense.splits,
    });
    
    setEditExpenseOpen(true);
  };

  const resetExpenseForm = () => {
    // Auto-select all members for split by default
    const defaultSplits = trip?.members.map(m => ({ user_id: m.user_id, amount: 0 })) || [];
    
    setNewExpense({
      description: "",
      total_amount: "",
      currency: trip?.currency || "USD",
      category: "general",
      payers: [],
      splits: defaultSplits,
    });
    setMultiplePayersMode(false);
    setSinglePayer("");
  };

  // Auto-calculate equal splits when amount changes or splits change
  const autoCalculateEqualSplits = (amount, splits) => {
    if (!amount || splits.length === 0) return splits;
    const perPerson = parseFloat(amount) / splits.length;
    return splits.map(s => ({ ...s, amount: perPerson }));
  };

  // Update splits when total amount changes
  const handleAmountChange = (value) => {
    const newSplits = autoCalculateEqualSplits(value, newExpense.splits);
    setNewExpense(prev => ({
      ...prev,
      total_amount: value,
      splits: newSplits
    }));
  };

  // Handle payer selection
  const handlePayerToggle = (member, checked) => {
    if (checked) {
      setNewExpense((prev) => ({
        ...prev,
        payers: [...prev.payers, { user_id: member.user_id, amount: 0 }],
      }));
    } else {
      setNewExpense((prev) => ({
        ...prev,
        payers: prev.payers.filter((p) => p.user_id !== member.user_id),
      }));
    }
  };

  const handlePayerAmountChange = (userId, amount) => {
    setNewExpense((prev) => ({
      ...prev,
      payers: prev.payers.map((p) =>
        p.user_id === userId ? { ...p, amount: parseFloat(amount) || 0 } : p
      ),
    }));
  };

  // Handle split selection
  const handleSplitToggle = (member, checked) => {
    let newSplits;
    if (checked) {
      newSplits = [...newExpense.splits, { user_id: member.user_id, amount: 0 }];
    } else {
      newSplits = newExpense.splits.filter((s) => s.user_id !== member.user_id);
    }
    
    // Auto-recalculate equal splits
    const calculatedSplits = autoCalculateEqualSplits(newExpense.total_amount, newSplits);
    setNewExpense((prev) => ({
      ...prev,
      splits: calculatedSplits,
    }));
  };

  // Auto-calculate equal splits
  const calculateEqualSplits = () => {
    const total = parseFloat(newExpense.total_amount) || 0;
    const splitCount = newExpense.splits.length;
    if (splitCount === 0) return;

    const perPerson = total / splitCount;
    setNewExpense((prev) => ({
      ...prev,
      splits: prev.splits.map((s) => ({ ...s, amount: perPerson })),
    }));
  };

  // Handle member addition
  const handleAddMember = async (e) => {
    e.preventDefault();

    if (!newMember.email || !newMember.name) {
      toast.error("Please fill in all fields");
      return;
    }

    try {
      await axios.post(
        `${API}/trips/${tripId}/members`,
        newMember,
        { withCredentials: true }
      );

      toast.success("Member added successfully!");
      setAddMemberOpen(false);
      setNewMember({ email: "", name: "" });
      fetchTrip();
    } catch (error) {
      console.error("Error adding member:", error);
      toast.error(error.response?.data?.detail || "Failed to add member");
    }
  };

  // Handle refund creation
  const handleCreateRefund = async (e) => {
    e.preventDefault();

    if (!newRefund.amount || !newRefund.reason || newRefund.refunded_to.length === 0) {
      toast.error("Please fill in all fields and select recipients");
      return;
    }

    try {
      const payload = {
        expense_id: selectedExpense.expense_id,
        amount: parseFloat(newRefund.amount),
        reason: newRefund.reason,
        refunded_to: newRefund.refunded_to,
      };

      await axios.post(`${API}/refunds`, payload, { withCredentials: true });

      toast.success("Refund added successfully!");
      setAddRefundOpen(false);
      setSelectedExpense(null);
      setNewRefund({ amount: "", reason: "", refunded_to: [] });
      fetchExpenses();
      fetchBalances();
      fetchSettlements();
    } catch (error) {
      console.error("Error creating refund:", error);
      toast.error("Failed to add refund");
    }
  };

  // Handle expense deletion
  const handleDeleteExpense = async (expenseId) => {
    try {
      await axios.delete(`${API}/expenses/${expenseId}`, {
        withCredentials: true,
      });
      toast.success("Expense deleted");
      fetchExpenses();
      fetchBalances();
      fetchSettlements();
      fetchTrip();
    } catch (error) {
      console.error("Error deleting expense:", error);
      toast.error("Failed to delete expense");
    }
  };

  // Handle trip deletion
  const handleDeleteTrip = async () => {
    try {
      await axios.delete(`${API}/trips/${tripId}`, { withCredentials: true });
      toast.success("Trip deleted");
      navigate("/dashboard");
    } catch (error) {
      console.error("Error deleting trip:", error);
      toast.error("Failed to delete trip");
    }
  };

  const getMemberName = (userId) => {
    const member = trip?.members.find((m) => m.user_id === userId);
    return member?.name || "Unknown";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!trip) {
    return null;
  }

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
              <Wallet className="w-6 h-6 text-primary" />
              <span className="font-heading text-lg font-bold tracking-tight">
                {trip.name}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Dialog open={addMemberOpen} onOpenChange={setAddMemberOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" data-testid="add-member-btn">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Add Member
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="font-heading text-2xl">
                    Add Member
                  </DialogTitle>
                  <DialogDescription>
                    Add a new member to this trip
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleAddMember} className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label htmlFor="member-name">Name</Label>
                    <Input
                      id="member-name"
                      placeholder="John Doe"
                      value={newMember.name}
                      onChange={(e) =>
                        setNewMember({ ...newMember, name: e.target.value })
                      }
                      data-testid="member-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="member-email">Email</Label>
                    <Input
                      id="member-email"
                      type="email"
                      placeholder="john@example.com"
                      value={newMember.email}
                      onChange={(e) =>
                        setNewMember({ ...newMember, email: e.target.value })
                      }
                      data-testid="member-email-input"
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full rounded-full font-bold btn-glow"
                    data-testid="submit-add-member-btn"
                  >
                    Add Member
                  </Button>
                </form>
              </DialogContent>
            </Dialog>

            {trip.created_by === user?.user_id && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="icon" className="text-destructive">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Trip?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently delete this trip and all its expenses.
                      This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDeleteTrip}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      data-testid="confirm-delete-trip-btn"
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Trip Stats */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 stagger-children">
          <div className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0">
            <p className="text-sm text-muted-foreground mb-1">Total Expenses</p>
            <p className="font-heading text-2xl font-bold" data-testid="trip-total-expenses">
              {getCurrencySymbol(trip.currency)}
              {trip.total_expenses.toFixed(2)}
            </p>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0">
            <p className="text-sm text-muted-foreground mb-1">Your Balance</p>
            <p
              className={`font-heading text-2xl font-bold ${
                trip.your_balance >= 0 ? "balance-positive" : "balance-negative"
              }`}
              data-testid="trip-your-balance"
            >
              {trip.your_balance >= 0 ? "+" : ""}
              {getCurrencySymbol(trip.currency)}
              {Math.abs(trip.your_balance).toFixed(2)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {trip.your_balance >= 0 ? "You are owed" : "You owe"}
            </p>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0">
            <p className="text-sm text-muted-foreground mb-1">Members</p>
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {trip.members.slice(0, 4).map((member) => (
                  <Avatar key={member.user_id} className="w-8 h-8 border-2 border-card">
                    <AvatarImage src={member.picture} />
                    <AvatarFallback className="text-xs">
                      {member.name.charAt(0)}
                    </AvatarFallback>
                  </Avatar>
                ))}
                {trip.members.length > 4 && (
                  <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-xs font-medium border-2 border-card">
                    +{trip.members.length - 4}
                  </div>
                )}
              </div>
              <span className="font-heading text-xl font-bold">{trip.members.length}</span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0">
            <p className="text-sm text-muted-foreground mb-1">Currency</p>
            <div className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-primary" />
              <span className="font-heading text-xl font-bold">{trip.currency}</span>
            </div>
          </div>
        </div>

        {/* Add Expense Button */}
        <div className="mb-8">
          <Dialog open={addExpenseOpen} onOpenChange={(open) => {
            setAddExpenseOpen(open);
            if (open && trip) {
              // Initialize with all members selected for split
              const defaultSplits = trip.members.map(m => ({ user_id: m.user_id, amount: 0 }));
              setNewExpense({
                description: "",
                total_amount: "",
                currency: trip.currency || "USD",
                category: "general",
                payers: [],
                splits: defaultSplits,
              });
            }
          }}>
            <DialogTrigger asChild>
              <Button
                className="w-full sm:w-auto rounded-full font-bold tracking-wide btn-glow"
                data-testid="add-expense-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Expense
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
              <DialogHeader className="sticky top-0 bg-card z-10 pb-4">
                <DialogTitle className="font-heading text-2xl">
                  Add Expense
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateExpense} className="space-y-6 pb-4">
                  {/* Description */}
                  <div className="space-y-2">
                    <Label htmlFor="expense-description">Description</Label>
                    <Input
                      id="expense-description"
                      placeholder="Hotel booking, dinner, etc."
                      value={newExpense.description}
                      onChange={(e) =>
                        setNewExpense({ ...newExpense, description: e.target.value })
                      }
                      data-testid="expense-description-input"
                    />
                  </div>

                  {/* Amount and Currency */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="expense-amount">Amount</Label>
                      <Input
                        id="expense-amount"
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={newExpense.total_amount}
                        onChange={(e) => handleAmountChange(e.target.value)}
                        data-testid="expense-amount-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Currency</Label>
                      <Select
                        value={newExpense.currency}
                        onValueChange={(value) =>
                          setNewExpense({ ...newExpense, currency: value })
                        }
                      >
                        <SelectTrigger data-testid="expense-currency-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {currencies.map((c) => (
                            <SelectItem key={c.code} value={c.code}>
                              {c.symbol} {c.code}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Who Paid */}
                  <div className="space-y-3">
                    <Label>Who paid?</Label>
                    <div className="space-y-2">
                      {trip.members.map((member) => {
                        const isSelected = newExpense.payers.some(
                          (p) => p.user_id === member.user_id
                        );
                        const payerData = newExpense.payers.find(
                          (p) => p.user_id === member.user_id
                        );

                        return (
                          <div
                            key={member.user_id}
                            className="flex items-center gap-3 p-3 bg-secondary/50 rounded-lg"
                          >
                            <Checkbox
                              checked={isSelected}
                              onCheckedChange={(checked) =>
                                handlePayerToggle(member, checked)
                              }
                              data-testid={`payer-checkbox-${member.user_id}`}
                            />
                            <Avatar className="w-8 h-8">
                              <AvatarImage src={member.picture} />
                              <AvatarFallback>{member.name.charAt(0)}</AvatarFallback>
                            </Avatar>
                            <span className="flex-1 text-sm">{member.name}</span>
                            {isSelected && (
                              <Input
                                type="number"
                                step="0.01"
                                placeholder="Amount"
                                value={payerData?.amount || ""}
                                onChange={(e) =>
                                  handlePayerAmountChange(member.user_id, e.target.value)
                                }
                                className="w-24 h-8 text-sm"
                                data-testid={`payer-amount-${member.user_id}`}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Split Between */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>Split between</Label>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={calculateEqualSplits}
                        className="text-xs text-primary"
                        data-testid="split-equally-btn"
                      >
                        Split Equally
                      </Button>
                    </div>
                    <div className="space-y-2">
                      {trip.members.map((member) => {
                        const isSelected = newExpense.splits.some(
                          (s) => s.user_id === member.user_id
                        );
                        const splitData = newExpense.splits.find(
                          (s) => s.user_id === member.user_id
                        );

                        return (
                          <div
                            key={member.user_id}
                            className="flex items-center gap-3 p-3 bg-secondary/50 rounded-lg"
                          >
                            <Checkbox
                              checked={isSelected}
                              onCheckedChange={(checked) =>
                                handleSplitToggle(member, checked)
                              }
                              data-testid={`split-checkbox-${member.user_id}`}
                            />
                            <Avatar className="w-8 h-8">
                              <AvatarImage src={member.picture} />
                              <AvatarFallback>{member.name.charAt(0)}</AvatarFallback>
                            </Avatar>
                            <span className="flex-1 text-sm">{member.name}</span>
                            {isSelected && (
                              <span className="text-sm font-medium text-primary">
                                {getCurrencySymbol(newExpense.currency)}
                                {(splitData?.amount || 0).toFixed(2)}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <Button
                    type="submit"
                    className="w-full rounded-full font-bold btn-glow sticky bottom-0"
                    data-testid="submit-expense-btn"
                  >
                    Add Expense
                  </Button>
                </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="expenses" className="space-y-6">
          <TabsList className="bg-secondary/50 p-1 rounded-full">
            <TabsTrigger
              value="expenses"
              className="rounded-full data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              data-testid="expenses-tab"
            >
              <Receipt className="w-4 h-4 mr-2" />
              Expenses
            </TabsTrigger>
            <TabsTrigger
              value="balances"
              className="rounded-full data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              data-testid="balances-tab"
            >
              <Users className="w-4 h-4 mr-2" />
              Balances
            </TabsTrigger>
            <TabsTrigger
              value="settlements"
              className="rounded-full data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
              data-testid="settlements-tab"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Settle Up
            </TabsTrigger>
          </TabsList>

          {/* Expenses Tab */}
          <TabsContent value="expenses" className="space-y-4">
            {expenses.length === 0 ? (
              <div className="bg-card border border-border rounded-xl p-12 text-center">
                <Receipt className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-heading text-xl font-bold mb-2">
                  No expenses yet
                </h3>
                <p className="text-muted-foreground">
                  Add your first expense to start tracking
                </p>
              </div>
            ) : (
              <div className="space-y-4 stagger-children">
                {expenses.map((expense) => (
                  <div
                    key={expense.expense_id}
                    className="bg-card border border-border rounded-xl p-6 card-hover animate-fade-in opacity-0"
                    data-testid={`expense-card-${expense.expense_id}`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="font-heading text-lg font-bold mb-1">
                          {expense.description}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {format(new Date(expense.date), "MMM d, yyyy")}
                          </span>
                          <span>
                            Paid by:{" "}
                            {expense.payers.map((p) => getMemberName(p.user_id)).join(", ")}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-heading text-xl font-bold">
                          {getCurrencySymbol(expense.currency)}
                          {expense.total_amount.toFixed(2)}
                        </p>
                        {expense.refunds.length > 0 && (
                          <p className="text-sm text-primary">
                            -{getCurrencySymbol(expense.currency)}
                            {(expense.total_amount - expense.net_amount).toFixed(2)} refunded
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Split details */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {expense.splits.map((split) => (
                        <span
                          key={split.user_id}
                          className="text-xs bg-secondary px-2 py-1 rounded-full"
                        >
                          {getMemberName(split.user_id)}:{" "}
                          {getCurrencySymbol(expense.currency)}
                          {split.amount.toFixed(2)}
                        </span>
                      ))}
                    </div>

                    {/* Refunds */}
                    {expense.refunds.length > 0 && (
                      <div className="mb-4 p-4 bg-secondary/50 rounded-lg border border-primary/20">
                        <p className="text-sm font-medium text-primary mb-2 flex items-center gap-2">
                          <RefreshCw className="w-4 h-4" />
                          Refunds
                        </p>
                        {expense.refunds.map((refund) => (
                          <div
                            key={refund.refund_id}
                            className="text-sm text-muted-foreground"
                            data-testid={`refund-${refund.refund_id}`}
                          >
                            <span className="text-primary font-medium">
                              {getCurrencySymbol(expense.currency)}
                              {refund.amount.toFixed(2)}
                            </span>{" "}
                            - {refund.reason}
                            <span className="text-xs ml-2">
                              (to: {refund.refunded_to.map((id) => getMemberName(id)).join(", ")})
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2 pt-4 border-t border-border">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedExpense(expense);
                          setAddRefundOpen(true);
                        }}
                        className="rounded-full"
                        data-testid={`add-refund-btn-${expense.expense_id}`}
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Add Refund
                      </Button>
                      {expense.created_by === user?.user_id && (
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-destructive rounded-full"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Expense?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This will delete this expense and all its refunds.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteExpense(expense.expense_id)}
                                className="bg-destructive"
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Balances Tab */}
          <TabsContent value="balances" className="space-y-4">
            <div className="bg-card border border-border rounded-xl divide-y divide-border">
              {balances.map((balance) => (
                <div
                  key={balance.user_id}
                  className="flex items-center justify-between p-4"
                  data-testid={`balance-${balance.user_id}`}
                >
                  <div className="flex items-center gap-3">
                    <Avatar className="w-10 h-10">
                      <AvatarImage
                        src={
                          trip.members.find((m) => m.user_id === balance.user_id)
                            ?.picture
                        }
                      />
                      <AvatarFallback>{balance.name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{balance.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {balance.balance >= 0 ? "is owed" : "owes"}
                      </p>
                    </div>
                  </div>
                  <p
                    className={`font-heading text-xl font-bold ${
                      balance.balance >= 0 ? "balance-positive" : "balance-negative"
                    }`}
                  >
                    {balance.balance >= 0 ? "+" : ""}
                    {getCurrencySymbol(trip.currency)}
                    {Math.abs(balance.balance).toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </TabsContent>

          {/* Settlements Tab */}
          <TabsContent value="settlements" className="space-y-4">
            {settlements.length === 0 ? (
              <div className="bg-card border border-border rounded-xl p-12 text-center">
                <RefreshCw className="w-12 h-12 text-primary mx-auto mb-4" />
                <h3 className="font-heading text-xl font-bold mb-2">
                  All settled up!
                </h3>
                <p className="text-muted-foreground">
                  No payments needed between group members
                </p>
              </div>
            ) : (
              <div className="space-y-4 stagger-children">
                {settlements.map((settlement, index) => (
                  <div
                    key={index}
                    className="bg-card border border-border rounded-xl p-6 animate-fade-in opacity-0"
                    data-testid={`settlement-${index}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Avatar className="w-10 h-10 border-2 border-destructive">
                          <AvatarImage
                            src={
                              trip.members.find(
                                (m) => m.user_id === settlement.from_user_id
                              )?.picture
                            }
                          />
                          <AvatarFallback>
                            {settlement.from_user_name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex items-center gap-3">
                          <ArrowRight className="w-5 h-5 text-muted-foreground" />
                        </div>
                        <Avatar className="w-10 h-10 border-2 border-primary">
                          <AvatarImage
                            src={
                              trip.members.find(
                                (m) => m.user_id === settlement.to_user_id
                              )?.picture
                            }
                          />
                          <AvatarFallback>
                            {settlement.to_user_name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                      </div>
                      <div className="text-right">
                        <p className="font-heading text-xl font-bold text-primary">
                          {getCurrencySymbol(settlement.currency)}
                          {settlement.amount.toFixed(2)}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {settlement.from_user_name} pays {settlement.to_user_name}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Refund Dialog */}
        <Dialog open={addRefundOpen} onOpenChange={setAddRefundOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-heading text-2xl">
                Add Refund
              </DialogTitle>
              {selectedExpense && (
                <DialogDescription>
                  Refund for: {selectedExpense.description} (
                  {getCurrencySymbol(selectedExpense.currency)}
                  {selectedExpense.total_amount.toFixed(2)})
                </DialogDescription>
              )}
            </DialogHeader>
            <form onSubmit={handleCreateRefund} className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="refund-amount">Refund Amount</Label>
                <Input
                  id="refund-amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={newRefund.amount}
                  onChange={(e) =>
                    setNewRefund({ ...newRefund, amount: e.target.value })
                  }
                  data-testid="refund-amount-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="refund-reason">Reason</Label>
                <Textarea
                  id="refund-reason"
                  placeholder="e.g., Cancelled booking, partial refund..."
                  value={newRefund.reason}
                  onChange={(e) =>
                    setNewRefund({ ...newRefund, reason: e.target.value })
                  }
                  data-testid="refund-reason-input"
                />
              </div>

              <div className="space-y-2">
                <Label>Who receives the refund?</Label>
                <div className="space-y-2">
                  {trip?.members.map((member) => {
                    const isSelected = newRefund.refunded_to.includes(member.user_id);
                    return (
                      <div
                        key={member.user_id}
                        className="flex items-center gap-3 p-3 bg-secondary/50 rounded-lg"
                      >
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setNewRefund({
                                ...newRefund,
                                refunded_to: [...newRefund.refunded_to, member.user_id],
                              });
                            } else {
                              setNewRefund({
                                ...newRefund,
                                refunded_to: newRefund.refunded_to.filter(
                                  (id) => id !== member.user_id
                                ),
                              });
                            }
                          }}
                          data-testid={`refund-recipient-${member.user_id}`}
                        />
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={member.picture} />
                          <AvatarFallback>{member.name.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <span className="text-sm">{member.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <Button
                type="submit"
                className="w-full rounded-full font-bold btn-glow"
                data-testid="submit-refund-btn"
              >
                Add Refund
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
};

export default TripDetail;
