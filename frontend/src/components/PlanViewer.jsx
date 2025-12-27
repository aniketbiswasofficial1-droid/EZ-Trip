import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Plane,
    Hotel,
    Utensils,
    Activity,
    Car,
    CloudSun,
    Package,
} from "lucide-react";
import { format } from "date-fns";

export const PlanViewer = ({ plan }) => {
    if (!plan) return null;

    const getCurrencySymbol = (curr) => {
        const symbols = { USD: "$", EUR: "€", GBP: "£", INR: "₹", JPY: "¥", AUD: "A$", SGD: "S$", THB: "฿" };
        return symbols[curr] || curr;
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

            {/* Cost Summary */}
            {plan.cost_breakdown && (
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
                                    {item.value?.toLocaleString() || 0}
                                </p>
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

                            {plan.cost_breakdown?.connectivity_suggestions && plan.cost_breakdown.connectivity_suggestions.length > 0 ? (
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
                                    No connectivity suggestions available
                                </p>
                            )}
                        </div>
                    </div>
                </TabsContent>

                {/* Itinerary Tab */}
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
                                                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                                        <span>{activity.duration}</span>
                                                        <span className="text-primary font-medium">
                                                            {getCurrencySymbol(plan.cost_breakdown?.currency || "INR")}
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

                {/* Activities Tab */}
                <TabsContent value="activities">
                    <ScrollArea className="h-[500px] pr-4">
                        <div className="space-y-4">
                            {plan.cost_breakdown?.activities_breakdown && plan.cost_breakdown.activities_breakdown.length > 0 ? (
                                plan.cost_breakdown.activities_breakdown.map((category, idx) => (
                                    <div key={idx} className="bg-card border border-border rounded-xl p-6">
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="font-heading text-lg font-bold capitalize">{category.category}</h4>
                                            <span className="font-heading text-xl font-bold text-primary">
                                                {getCurrencySymbol(plan.cost_breakdown?.currency || "INR")}
                                                {category.cost?.toLocaleString()}
                                            </span>
                                        </div>
                                        <ul className="space-y-2">
                                            {category.activities?.map((activity, aidx) => (
                                                <li key={aidx} className="text-muted-foreground">• {activity}</li>
                                            ))}
                                        </ul>
                                    </div>
                                ))
                            ) : (
                                <p className="text-muted-foreground">No activities listed</p>
                            )}
                        </div>
                    </ScrollArea>
                </TabsContent>

                {/* Tips Tab */}
                <TabsContent value="tips">
                    <ScrollArea className="h-[500px] pr-4">
                        <div className="space-y-4">
                            {plan.travel_tips && plan.travel_tips.length > 0 ? (
                                <div className="bg-card border border-border rounded-xl p-6">
                                    <h4 className="font-heading text-lg font-bold mb-4">Travel Tips</h4>
                                    <ul className="space-y-2">
                                        {plan.travel_tips.map((tip, idx) => (
                                            <li key={idx} className="text-muted-foreground">💡 {tip}</li>
                                        ))}
                                    </ul>
                                </div>
                            ) : null}

                            {plan.local_customs && plan.local_customs.length > 0 ? (
                                <div className="bg-card border border-border rounded-xl p-6">
                                    <h4 className="font-heading text-lg font-bold mb-4">Local Customs & Etiquette</h4>
                                    <ul className="space-y-2">
                                        {plan.local_customs.map((custom, idx) => (
                                            <li key={idx} className="text-muted-foreground">🌍 {custom}</li>
                                        ))}
                                    </ul>
                                </div>
                            ) : null}

                            {(!plan.travel_tips || plan.travel_tips.length === 0) && (!plan.local_customs || plan.local_customs.length === 0) && (
                                <p className="text-muted-foreground">No tips available</p>
                            )}
                        </div>
                    </ScrollArea>
                </TabsContent>

                {/* Packing Tab */}
                <TabsContent value="packing">
                    <ScrollArea className="h-[500px] pr-4">
                        <div className="space-y-4">
                            {plan.packing_suggestions_detailed && plan.packing_suggestions_detailed.length > 0 ? (
                                plan.packing_suggestions_detailed.map((category, idx) => (
                                    <div key={idx} className="bg-card border border-border rounded-xl p-6">
                                        <h4 className="font-heading text-lg font-bold mb-3 capitalize">{category.category}</h4>
                                        <ul className="grid sm:grid-cols-2 gap-2">
                                            {category.items?.map((item, iIdx) => (
                                                <li key={iIdx} className="text-muted-foreground">📦 {item}</li>
                                            ))}
                                        </ul>
                                    </div>
                                ))
                            ) : plan.packing_suggestions && plan.packing_suggestions.length > 0 ? (
                                <div className="bg-card border border-border rounded-xl p-6">
                                    <h4 className="font-heading text-lg font-bold mb-3">Packing List</h4>
                                    <ul className="grid sm:grid-cols-2 gap-2">
                                        {plan.packing_suggestions.map((item, idx) => (
                                            <li key={idx} className="text-muted-foreground">📦 {item}</li>
                                        ))}
                                    </ul>
                                </div>
                            ) : (
                                <p className="text-muted-foreground">No packing list available</p>
                            )}
                        </div>
                    </ScrollArea>
                </TabsContent>

                {/* Info Tab */}
                <TabsContent value="info">
                    <div className="space-y-4">
                        {plan.best_time_to_visit && (
                            <div className="bg-card border border-border rounded-xl p-6">
                                <h4 className="font-heading text-lg font-bold mb-3 flex items-center gap-2">
                                    <CloudSun className="w-5 h-5 text-primary" />
                                    Best Time to Visit
                                </h4>
                                <p className="text-muted-foreground">{plan.best_time_to_visit}</p>
                            </div>
                        )}

                        {plan.weather_summary && (
                            <div className="bg-card border border-border rounded-xl p-6">
                                <h4 className="font-heading text-lg font-bold mb-3 flex items-center gap-2">
                                    <CloudSun className="w-5 h-5 text-primary" />
                                    Weather Summary
                                </h4>
                                <p className="text-muted-foreground">{plan.weather_summary}</p>
                            </div>
                        )}

                        {plan.emergency_contacts && Object.keys(plan.emergency_contacts).length > 0 && (
                            <div className="bg-card border border-border rounded-xl p-6">
                                <h4 className="font-heading text-lg font-bold mb-4">Emergency Contacts</h4>
                                <div className="space-y-2">
                                    {Object.entries(plan.emergency_contacts).map(([key, value]) => (
                                        <div key={key} className="flex justify-between">
                                            <span className="capitalize text-muted-foreground">{key.replace(/_/g, ' ')}</span>
                                            <span className="font-mono">{value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {!plan.best_time_to_visit && !plan.weather_summary && (!plan.emergency_contacts || Object.keys(plan.emergency_contacts).length === 0) && (
                            <p className="text-muted-foreground">No local information available</p>
                        )}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};
