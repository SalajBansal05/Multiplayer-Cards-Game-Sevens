import Card from "./Card";

function Pile({suit, low, high}) {
    if (low === null){
        return <div className="pile">Play 7{suit} to start</div>
    }

    if (low === high){
        return (
            <div className="pile">
                <Card card={`${low}${suit}`} />
            </div>
        );
    }

    return (
        <div className="pile">
            <Card card = { `${low}${suit}` } />

            <span className="dots">...</span>

            <Card card = {`${high}${suit}`} />
        </div>
    )
}

export default Pile
