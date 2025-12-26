import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MapPin, Star, Loader2, X } from "lucide-react";
import { toast } from "sonner";

/**
 * LocationAutocomplete Component
 * 
 * A reusable autocomplete component for location selection with:
 * - Debounced search (300ms)
 * - Favorite locations support
 * - Required selection from suggestions (no free text)
 * 
 * @param {string} value - The display name of selected location
 * @param {function} onChange - Callback when location is selected
 * @param {string} placeholder - Input placeholder text
 * @param {string} className - Additional CSS classes
 * @param {object} icon - Icon component to display
 * @param {boolean} error - Whether field has error state
 */
export const LocationAutocomplete = ({
    value = "",
    onChange,
    placeholder = "Search for a location",
    className = "",
    icon: Icon = MapPin,
    error = false,
}) => {
    const [inputValue, setInputValue] = useState(value);
    const [suggestions, setSuggestions] = useState([]);
    const [favorites, setFavorites] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [highlightedIndex, setHighlightedIndex] = useState(-1);

    const dropdownRef = useRef(null);
    const inputRef = useRef(null);
    const debounceTimerRef = useRef(null);

    // Load favorite locations on mount
    useEffect(() => {
        loadFavorites();
    }, []);

    // Update input value when prop changes
    useEffect(() => {
        if (value !== inputValue) {
            setInputValue(value);
        }
    }, [value]);

    // Handle click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(event.target) &&
                !inputRef.current.contains(event.target)
            ) {
                setShowDropdown(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const loadFavorites = async () => {
        try {
            const response = await axios.get(`${API}/user/favorite-locations`, {
                withCredentials: true,
            });
            setFavorites(response.data.favorites || []);
        } catch (error) {
            console.error("Error loading favorites:", error);
            // Don't show error toast - favorites are optional
        }
    };

    const searchLocations = async (query) => {
        if (!query || query.trim().length < 2) {
            setSuggestions([]);
            return;
        }

        setLoading(true);
        try {
            console.log('Searching locations with query:', query);
            console.log('API URL:', `${API}/locations/search`);

            const response = await axios.get(`${API}/locations/search`, {
                params: { q: query },
                withCredentials: true,
            });

            console.log('Location search response:', response.data);
            setSuggestions(response.data.locations || []);
        } catch (error) {
            console.error("Error searching locations:", error);
            console.error("Error details:", {
                message: error.message,
                response: error.response?.data,
                status: error.response?.status,
                url: error.config?.url
            });
            toast.error(`Failed to search locations: ${error.response?.data?.detail || error.message}`);
            setSuggestions([]);
        } finally {
            setLoading(false);
        }
    };

    const debouncedSearch = useCallback((query) => {
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        debounceTimerRef.current = setTimeout(() => {
            searchLocations(query);
        }, 300);
    }, []);

    const handleInputChange = (e) => {
        const newValue = e.target.value;
        setInputValue(newValue);
        setShowDropdown(true);
        setHighlightedIndex(-1);

        // Clear selected location if user types
        if (selectedLocation) {
            setSelectedLocation(null);
            onChange(null);
        }

        debouncedSearch(newValue);
    };

    const handleSelectLocation = (location) => {
        setSelectedLocation(location);
        setInputValue(location.display_name);
        setShowDropdown(false);
        setSuggestions([]);
        setHighlightedIndex(-1);
        onChange(location);
    };

    const handleClear = () => {
        setInputValue("");
        setSelectedLocation(null);
        setSuggestions([]);
        setShowDropdown(false);
        onChange(null);
        inputRef.current?.focus();
    };

    const toggleFavorite = async (location, e) => {
        e.stopPropagation();

        const isFavorite = favorites.some((fav) => fav.id === location.id);

        try {
            if (isFavorite) {
                await axios.delete(`${API}/user/favorite-locations/${location.id}`, {
                    withCredentials: true,
                });
                setFavorites(favorites.filter((fav) => fav.id !== location.id));
                toast.success("Removed from favorites");
            } else {
                await axios.post(`${API}/user/favorite-locations`, location, {
                    withCredentials: true,
                });
                setFavorites([...favorites, location]);
                toast.success("Added to favorites");
            }
        } catch (error) {
            console.error("Error toggling favorite:", error);
            toast.error("Failed to update favorites");
        }
    };

    const handleKeyDown = (e) => {
        const allSuggestions = [
            ...favorites.filter((fav) =>
                fav.display_name.toLowerCase().includes(inputValue.toLowerCase())
            ),
            ...suggestions,
        ];

        if (!showDropdown || allSuggestions.length === 0) return;

        switch (e.key) {
            case "ArrowDown":
                e.preventDefault();
                setHighlightedIndex((prev) =>
                    prev < allSuggestions.length - 1 ? prev + 1 : prev
                );
                break;
            case "ArrowUp":
                e.preventDefault();
                setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : -1));
                break;
            case "Enter":
                e.preventDefault();
                if (highlightedIndex >= 0 && highlightedIndex < allSuggestions.length) {
                    handleSelectLocation(allSuggestions[highlightedIndex]);
                }
                break;
            case "Escape":
                setShowDropdown(false);
                setHighlightedIndex(-1);
                break;
            default:
                break;
        }
    };

    // Filter favorites based on current input
    const filteredFavorites = favorites.filter((fav) =>
        inputValue.length > 0
            ? fav.display_name.toLowerCase().includes(inputValue.toLowerCase())
            : true
    );

    const showFavorites = filteredFavorites.length > 0 && showDropdown;
    const showSuggestions = suggestions.length > 0 && showDropdown;
    const showNoResults =
        !loading && !showFavorites && !showSuggestions && inputValue.length >= 2 && showDropdown;

    return (
        <div className="relative">
            <div className="relative">
                <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground z-10" />
                <Input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={handleInputChange}
                    onFocus={() => {
                        setShowDropdown(true);
                        if (inputValue.length >= 2) {
                            debouncedSearch(inputValue);
                        }
                    }}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    className={`pl-10 pr-10 h-12 ${error ? "border-destructive" : ""} ${className}`}
                    autoComplete="off"
                />
                {loading && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground animate-spin" />
                )}
                {!loading && inputValue && (
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8"
                        onClick={handleClear}
                    >
                        <X className="w-4 h-4" />
                    </Button>
                )}
            </div>

            {/* Dropdown */}
            {(showFavorites || showSuggestions || showNoResults) && (
                <div
                    ref={dropdownRef}
                    className="absolute z-50 w-full mt-2 bg-card border border-border rounded-lg shadow-lg overflow-hidden animate-in fade-in-0 slide-in-from-top-2"
                >
                    <ScrollArea className="max-h-[300px]">
                        {/* Favorites Section */}
                        {showFavorites && (
                            <div>
                                <div className="px-3 py-2 text-xs font-semibold text-muted-foreground bg-secondary/50">
                                    Favorites
                                </div>
                                {filteredFavorites.map((location, index) => {
                                    const isHighlighted = index === highlightedIndex;
                                    return (
                                        <button
                                            key={`fav-${location.id}`}
                                            type="button"
                                            onClick={() => handleSelectLocation(location)}
                                            className={`w-full px-3 py-3 flex items-start gap-3 hover:bg-secondary/50 transition-colors text-left ${isHighlighted ? "bg-secondary/50" : ""
                                                }`}
                                        >
                                            <MapPin className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">
                                                    {location.name}
                                                </p>
                                                <p className="text-xs text-muted-foreground truncate">
                                                    {location.display_name}
                                                </p>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={(e) => toggleFavorite(location, e)}
                                                className="shrink-0 p-1 hover:bg-secondary/50 rounded transition-colors"
                                            >
                                                <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                                            </button>
                                        </button>
                                    );
                                })}
                            </div>
                        )}

                        {/* Suggestions Section */}
                        {showSuggestions && (
                            <div>
                                {showFavorites && (
                                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground bg-secondary/50 border-t">
                                        Suggestions
                                    </div>
                                )}
                                {suggestions.map((location, index) => {
                                    const adjustedIndex = showFavorites
                                        ? filteredFavorites.length + index
                                        : index;
                                    const isHighlighted = adjustedIndex === highlightedIndex;
                                    const isFavorite = favorites.some((fav) => fav.id === location.id);

                                    return (
                                        <button
                                            key={`sug-${location.id}`}
                                            type="button"
                                            onClick={() => handleSelectLocation(location)}
                                            className={`w-full px-3 py-3 flex items-start gap-3 hover:bg-secondary/50 transition-colors text-left ${isHighlighted ? "bg-secondary/50" : ""
                                                }`}
                                        >
                                            <MapPin className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">
                                                    {location.name}
                                                </p>
                                                <p className="text-xs text-muted-foreground truncate">
                                                    {location.display_name}
                                                </p>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={(e) => toggleFavorite(location, e)}
                                                className="shrink-0 p-1 hover:bg-secondary/50 rounded transition-colors"
                                            >
                                                <Star
                                                    className={`w-4 h-4 ${isFavorite
                                                        ? "fill-yellow-500 text-yellow-500"
                                                        : "text-muted-foreground"
                                                        }`}
                                                />
                                            </button>
                                        </button>
                                    );
                                })}
                            </div>
                        )}

                        {/* No Results */}
                        {showNoResults && (
                            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                                No locations found
                            </div>
                        )}
                    </ScrollArea>
                </div>
            )}
        </div>
    );
};

export default LocationAutocomplete;
