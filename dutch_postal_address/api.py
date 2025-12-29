"""
REST API server for address validation and correction.
Uses FastAPI as specified in requirements.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from .address import DutchAddressHandler
from .validator import validate, validate_lines as validate_lines_func
from .corrector import correct_city as correct_city_func, correct_street as correct_street_func

# Initialize FastAPI app
app = FastAPI(
    title="Dutch Postal Address API",
    description="API for validating and correcting Dutch postal addresses",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handler
handler = DutchAddressHandler()


# Pydantic models for request/response
class AddressRequest(BaseModel):
    street_name: str
    house_number: int
    house_number_extension: str = ""
    postcode: str
    city: str


class AddressLinesRequest(BaseModel):
    lines: List[str]


class ValidationResponse(BaseModel):
    valid: bool
    normalized_address: Optional[dict] = None


class CorrectionResponse(BaseModel):
    input: str
    suggestions: List[str]
    count: int


class SearchResponse(BaseModel):
    query: str
    results: List[dict]
    count: int


# API endpoints
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "Dutch Postal Address API",
        "version": "1.0.0",
        "endpoints": {
            "/validate": "POST - Validate complete address",
            "/validate/lines": "POST - Validate address from lines",
            "/correct/city": "GET - Correct city name",
            "/correct/street": "GET - Correct street name",
            "/search": "GET - Search addresses"
        }
    }


@app.post("/validate", response_model=ValidationResponse)
async def validate_address(request: AddressRequest):
    """Validate a complete address."""
    try:
        is_valid = validate(
            street_name=request.street_name,
            house_number=request.house_number,
            house_number_extension=request.house_number_extension,
            postcode=request.postcode,
            city=request.city
        )

        response = {"valid": is_valid}

        if is_valid:
            from .address import Address
            address = Address(
                street_name=request.street_name,
                house_number=request.house_number,
                house_number_extension=request.house_number_extension,
                postcode=request.postcode,
                city=request.city
            )
            response["normalized_address"] = address.to_dict()

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/validate/lines", response_model=ValidationResponse)
async def validate_address_lines(request: AddressLinesRequest):
    """Validate address from two-line format."""
    try:
        is_valid = validate_lines_func(request.lines)

        response = {"valid": is_valid}

        if is_valid:
            from .address import Address
            try:
                address = Address.from_lines(request.lines)
                response["normalized_address"] = address.to_dict()
            except ValueError:
                pass

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/correct/city", response_model=CorrectionResponse)
async def correct_city_endpoint(
        city: str = Query(..., description="City name to correct"),
        postcode: Optional[str] = Query(None, description="Optional postcode filter (PC4 or PC6)")
):
    """Correct a city name."""
    try:
        suggestions = correct_city_func(city, postcode)
        return {
            "input": city,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/correct/street", response_model=CorrectionResponse)
async def correct_street_endpoint(
        street: str = Query(..., description="Street name to correct"),
        postcode: Optional[str] = Query(None, description="Optional postcode filter (PC4 or PC6)")
):
    """Correct a street name."""
    try:
        suggestions = correct_street_func(street, postcode)
        return {
            "input": street,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/search", response_model=SearchResponse)
async def search_addresses(
        q: str = Query(..., description="Search query"),
        limit: int = Query(10, description="Maximum results", ge=1, le=100)
):
    """Search addresses by partial input."""
    try:
        results = handler.search_addresses(q, limit)
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api()