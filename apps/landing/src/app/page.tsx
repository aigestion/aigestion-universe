import { NeuralHero } from '@/components/NeuralHero/NeuralHero'
import { FeaturesBento } from '@/components/Features/FeaturesBento'
import { Pricing } from '@/components/Pricing/Pricing'
import { Footer } from '@/components/Footer/Footer'
import { TrustBar } from '@/components/TrustBar'
import { DemoEmbed } from '@/components/DemoEmbed/DemoEmbed'
import { QRCodeSection } from '@/components/QRCode/QRCodeSection'

export default function Home() {
  return (
    <>
      <NeuralHero />
      <TrustBar />
      <section className="relative py-24 md:py-32 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-display font-light tracking-tight mb-6">
            Why <span className="text-gradient">aigestion.net</span>?
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Your agents are fragmented. 12 tools. 3 dashboards.  visibility.
            One gateway. 19 federated engines. Swarm consensus. Runs on your metal.
          </p>
        </div>
        <FeaturesBento />
      </section>
      <DemoEmbed />
      <section className="py-24 md:py-32 px-6 max-w-7xl mx-auto">
        <QRCodeSection />
      </section>
      <Pricing />
      <Footer />
    </>
  )
}
