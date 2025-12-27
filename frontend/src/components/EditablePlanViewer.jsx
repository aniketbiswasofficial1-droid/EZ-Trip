import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
    Plane,
    Hotel,
    Utensils,
    Activity,
    Car,
    CloudSun,
    Package,
    Edit2,
    Save,
    X,
    Plus,
    Trash2,
} from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";
import axios from "axios";
import { API } from "@/App";

export const EditablePlanViewer = ({ plan: initialPlan, tripId }) => {
    const [plan, setPlan] = useState(initialPlan);
    const [editMode, setEditMode] = useState({
        cost: false,
        routes: false,
        itinerary: false,
        activities: false,
        tips: false,
        packing: false,
        info: false,
    });
    const [saving, setSaving] = useState(false);

    if (!plan) return null;

    const getCurrencySymbol = (curr) => {
        const symbols = { USD: "$", EUR: "€", GBP: "£", INR: "₹", JPY: "¥", AUD: "A$", SGD: "S$", THB: "฿" };
        return symbols[curr] || curr;
    };

    // Save plan to backend
    const handleSave = async (section) => {
        setSaving(true);
        try {
            // Update plan via API
            await axios.put(`${API}/trips/${tripId}/plan`, plan, {
                withCredentials: true,
            });
            toast.success(`${section} saved successfully!`);
            setEditMode((prev) => ({ ...prev, [section]: false }));
        } catch (error) {
            console.error("Error saving plan:", error);
            toast.error("Failed to save changes");
        } finally {
            setSaving(false);
        }
    };

    const recalculateTotals = (updatedCost) => {
        const totalGroup =
            (updatedCost.departure_transport || 0) +
            (updatedCost.return_transport || 0) +
            (updatedCost.accommodation || 0) +
            (updatedCost.food || 0) +
            (updatedCost.activities || 0) +
            (updatedCost.local_transportation || 0) +
            (updatedCost.miscellaneous || 0);

        const numTravelers = plan.num_travelers || 1;
        const totalPerPerson = totalGroup / numTravelers;

        return {
            ...updatedCost,
            total_per_person: totalPerPerson,
            total_group: totalGroup,
        };
    };

    const handleCostUpdate = (field, value) => {
        setPlan((prev) => {
            const updatedCost = {
                ...prev.cost_breakdown,
                [field]: parseFloat(value) || 0,
            };
            return {
                ...prev,
                cost_breakdown: recalculateTotals(updatedCost),
            };
        });
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="font-heading text-3xl font-bold mb-1">
                    {plan.destination}
                </h2>
                <p className="text-muted-foreground">
                    {plan.num_days || plan.itinerary?.length || 0} days • {plan.num_travelers || 2} travelers
                </p>
            </div>

            {/* Cost Summary - Editable */}
            {plan.cost_breakdown && (
                <div className="bg-card border border-border rounded-xl p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-heading text-lg font-bold flex items-center gap-2">
                            <span className="text-2xl">{getCurrencySymbol(plan.cost_breakdown.currency)}</span>
                            Cost Estimate (Per Person)
                        </h3>
                        {!editMode.cost ? (
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setEditMode((prev) => ({ ...prev, cost: true }))}
                            >
                                <Edit2 className="w-4 h-4 mr-2" />
                                Edit
                            </Button>
                        ) : (
                            <div className="flex gap-2">
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                        setPlan(initialPlan);
                                        setEditMode((prev) => ({ ...prev, cost: false }));
                                    }}
                                >
                                    <X className="w-4 h-4 mr-2" />
                                    Cancel
                                </Button>
                                <Button
                                    size="sm"
                                    onClick={() => handleSave('cost')}
                                    disabled={saving}
                                >
                                    <Save className="w-4 h-4 mr-2" />
                                    Save
                                </Button>
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
                        {[
                            { label: "Departure", field: "departure_transport", value: plan.cost_breakdown.departure_transport, icon: Plane },
                            { label: "Return", field: "return_transport", value: plan.cost_breakdown.return_transport, icon: Plane },
                            { label: "Accommodation", field: "accommodation", value: plan.cost_breakdown.accommodation, icon: Hotel },
                            { label: "Food", field: "food", value: plan.cost_breakdown.food, icon: Utensils },
                            { label: "Activities", field: "activities", value: plan.cost_breakdown.activities, icon: Activity },
                            { label: "Local Transport", field: "local_transportation", value: plan.cost_breakdown.local_transportation, icon: Car },
                            { label: "Other", field: "miscellaneous", value: plan.cost_breakdown.miscellaneous, icon: Package },
                        ].map((item) => (
                            <div key={item.label} className="p-3 bg-secondary/50 rounded-lg">
                                <div className="flex items-center gap-2 mb-1">
                                    <item.icon className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-sm text-muted-foreground">{item.label}</span>
                                </div>
                                {editMode.cost ? (
                                    <Input
                                        type="text"
                                        inputMode="numeric"
                                        pattern="[0-9]*"
                                        value={item.value}
                                        onChange={(e) => handleCostUpdate(item.field, e.target.value)}
                                        className="font-heading font-bold h-8"
                                    />
                                ) : (
                                    <p className="font-heading font-bold">
                                        {getCurrencySymbol(plan.cost_breakdown.currency)}
                                        {item.value?.toLocaleString() || 0}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="flex justify-between items-center pt-4 border-t border-border">
                        <div>
                            <p className="text-sm text-muted-foreground">Per Person</p>
                            <p className="font-heading text-2xl font-bold text-primary">
                                {getCurrencySymbol(plan.cost_breakdown.currency)}
                                {plan.cost_breakdown.total_per_person?.toLocaleString() || 0}
                            </p>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-muted-foreground">Total Group</p>
                            <p className="font-heading text-2xl font-bold">
                                {getCurrencySymbol(plan.cost_breakdown.currency)}
                                {plan.cost_breakdown.total_group?.toLocaleString() || 0}
                            </p>
                        </div>
                    </div>
                </div>
            )}

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

                {/* Routes Tab - Simple view for now */}
                <TabsContent value="connectivity">
                    <div className="bg-card border border-border rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="font-heading text-lg font-bold">
                                🚆✈️ Transport Routes
                            </h4>
                        </div>
                        {plan.cost_breakdown?.connectivity_suggestions && plan.cost_breakdown.connectivity_suggestions.length > 0 ? (
                            <div className="space-y-4">
                                {plan.cost_breakdown.connectivity_suggestions.map((conn, idx) => (
                                    <div key={idx} className="p-4 bg-secondary/30 rounded-lg">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="font-bold capitalize">
                                                    {conn.transport_mode === 'flight' ? '✈️' : '🚆'} {conn.transport_mode}
                                                </p>
                                                <p className="text-sm text-muted-foreground">
                                                    {conn.from_location} → {conn.to_location}
                                                </p>
                                            </div>
                                            <span className="text-sm font-medium text-primary">
                                                ⏱️ {conn.journey_time_estimate}
                                            </span>
                                        </div>
                                        <p className="text-sm mt-2">{conn.connectivity_notes}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-muted-foreground text-center py-8">
                                No route information available
                            </p>
                        )}
                    </div>
                </TabsContent>

                {/* Other tabs remain view-only for MVP - can be enhanced later */}
                <TabsContent value="itinerary">
                    <ScrollArea className="h-[500px] pr-4">
                        <div className="space-y-4">
                            {plan.itinerary?.map((day) => (
                                <div
                                    key={day.day}
                                    className="bg-card border border-border rounded-xl p-6"
                                >
                                    <div className="flex items-center justify-between mb-4">
                                        <div>
                                            <h4 className="font-heading text-lg font-bold">
                                                Day {day.day}
                                            </h4>
                                            <p className="text-sm text-muted-foreground">
                                                {day.date && format(new Date(day.date), "EEEE, MMM d")}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        {day.activities?.map((activity, idx) => (
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
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                </TabsContent>

                {/* Activities, Tips, Packing, Info tabs - keeping from original PlanViewer */}
                <TabsContent value="activities">
                    <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4">Activities Overview</h4>
                        <p className="text-muted-foreground">Activity details shown in Day Plan</p>
                    </div>
                </TabsContent>

                <TabsContent value="tips">
                    <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4">Travel Tips</h4>
                        {plan.travel_tips && plan.travel_tips.length > 0 ? (
                            <ul className="space-y-2">
                                {plan.travel_tips.map((tip, idx) => (
                                    <li key={idx} className="text-muted-foreground">💡 {tip}</li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-muted-foreground">No tips available</p>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="packing">
                    <div className="bg-card border border-border rounded-xl p-6">
                        <h4 className="font-heading text-lg font-bold mb-4">Packing List</h4>
                        {plan.packing_suggestions_detailed && plan.packing_suggestions_detailed.length > 0 ? (
                            plan.packing_suggestions_detailed.map((category, idx) => (
                                <div key={idx} className="mb-4">
                                    <h5 className="font-bold mb-2 capitalize">{category.category}</h5>
                                    <ul className="grid sm:grid-cols-2 gap-2">
                                        {category.items?.map((item, iIdx) => (
                                            <li key={iIdx} className="text-muted-foreground">📦 {item}</li>
                                        ))}
                                    </ul>
                                </div>
                            ))
                        ) : (
                            <p className="text-muted-foreground">No packing list available</p>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="info">
                    <div className="space-y-4">
                        {plan.best_time_to_visit && (
                            <div className="bg-card border border-border rounded-xl p-6">
                                <h4 className="font-heading text-lg font-bold mb-3">Best Time to Visit</h4>
                                <p className="text-muted-foreground">{plan.best_time_to_visit}</p>
                            </div>
                        )}
                        {plan.weather_summary && (
                            <div className="bg-card border border-border rounded-xl p-6">
                                <h4 className="font-heading text-lg font-bold mb-3">Weather Summary</h4>
                                <p className="text-muted-foreground">{plan.weather_summary}</p>
                            </div>
                        )}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};
